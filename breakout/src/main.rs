use bevy::{
    prelude::*,
    window::WindowResolution,
};

// 游戏常量定义
const SCREEN_WIDTH: f32 = 900.0;
const SCREEN_HEIGHT: f32 = 700.0;

const PADDLE_SIZE: Vec2 = Vec2::new(120.0, 18.0);
const PADDLE_SPEED: f32 = 600.0;
const PADDLE_Y: f32 = -280.0;

const BALL_SIZE: Vec2 = Vec2::new(16.0, 16.0);
const BALL_INITIAL_SPEED: f32 = 450.0;
const BALL_INITIAL_DIRECTION: Vec2 = Vec2::new(0.5, 0.85);

const BRICK_ROWS: usize = 6;
const BRICK_COLS: usize = 12;
const BRICK_SIZE: Vec2 = Vec2::new(64.0, 22.0);
const BRICK_GAP: Vec2 = Vec2::new(8.0, 8.0);
const BRICK_OFFSET_Y: f32 = 120.0;

// 配色方案 (Modern Cyberpunk Gold / Neon palette)
const BACKGROUND_COLOR: Color = Color::srgb(0.06, 0.07, 0.11);
const PADDLE_COLOR: Color = Color::srgb(0.0, 0.85, 0.95);
const BALL_COLOR: Color = Color::srgb(1.0, 0.84, 0.0);
const WALL_COLOR: Color = Color::srgb(0.2, 0.25, 0.35);

const BRICK_COLORS: [Color; 6] = [
    Color::srgb(0.95, 0.26, 0.35), // Red / Pink
    Color::srgb(0.98, 0.55, 0.0),  // Orange
    Color::srgb(1.0, 0.78, 0.03),  // Gold
    Color::srgb(0.18, 0.80, 0.44), // Green
    Color::srgb(0.11, 0.63, 0.95), // Blue
    Color::srgb(0.61, 0.35, 0.95), // Purple
];

// 组件定义
#[derive(Component)]
struct Paddle;

#[derive(Component)]
struct Ball;

#[derive(Component, Deref, DerefMut)]
struct Velocity(Vec2);

#[derive(Component)]
struct Brick {
    points: u32,
}

#[derive(Component)]
struct Collider {
    size: Vec2,
}

#[derive(Component)]
enum WallLocation {
    Left,
    Right,
    Top,
}

#[derive(Resource, Default)]
struct Scoreboard {
    score: u32,
}

#[derive(Component)]
struct ScoreText;

// 碰撞判定方向
#[derive(Debug)]
enum Collision {
    Left,
    Right,
    Top,
    Bottom,
}

fn main() {
    App::new()
        .add_plugins(DefaultPlugins.set(WindowPlugin {
            primary_window: Some(Window {
                title: "Breakout - Bevy Game".into(),
                resolution: WindowResolution::new(SCREEN_WIDTH, SCREEN_HEIGHT),
                resizable: false,
                ..default()
            }),
            ..default()
        }))
        .insert_resource(ClearColor(BACKGROUND_COLOR))
        .insert_resource(Scoreboard::default())
        .add_systems(Startup, setup)
        .add_systems(
            Update,
            (
                move_paddle,
                apply_velocity,
                check_ball_collisions,
                update_scoreboard,
            )
                .chain(),
        )
        .run();
}

fn setup(
    mut commands: Commands,
) {
    // 2D 摄像机
    commands.spawn(Camera2dBundle::default());

    // 1. 生成挡板 Paddle
    commands.spawn((
        SpriteBundle {
            transform: Transform {
                translation: Vec3::new(0.0, PADDLE_Y, 0.0),
                scale: Vec3::new(PADDLE_SIZE.x, PADDLE_SIZE.y, 1.0),
                ..default()
            },
            sprite: Sprite {
                color: PADDLE_COLOR,
                ..default()
            },
            ..default()
        },
        Paddle,
        Collider { size: PADDLE_SIZE },
    ));

    // 2. 生成球 Ball
    let ball_direction = BALL_INITIAL_DIRECTION.normalize();
    commands.spawn((
        SpriteBundle {
            transform: Transform {
                translation: Vec3::new(0.0, PADDLE_Y + 30.0, 1.0),
                scale: Vec3::new(BALL_SIZE.x, BALL_SIZE.y, 1.0),
                ..default()
            },
            sprite: Sprite {
                color: BALL_COLOR,
                ..default()
            },
            ..default()
        },
        Ball,
        Velocity(ball_direction * BALL_INITIAL_SPEED),
        Collider { size: BALL_SIZE },
    ));

    // 3. 生成边界墙壁 Walls
    let wall_thickness = 20.0;
    let bounds = Vec2::new(SCREEN_WIDTH, SCREEN_HEIGHT);

    // 左墙
    commands.spawn((
        SpriteBundle {
            transform: Transform {
                translation: Vec3::new(-bounds.x / 2.0 + wall_thickness / 2.0, 0.0, 0.0),
                scale: Vec3::new(wall_thickness, bounds.y, 1.0),
                ..default()
            },
            sprite: Sprite { color: WALL_COLOR, ..default() },
            ..default()
        },
        WallLocation::Left,
        Collider { size: Vec2::new(wall_thickness, bounds.y) },
    ));

    // 右墙
    commands.spawn((
        SpriteBundle {
            transform: Transform {
                translation: Vec3::new(bounds.x / 2.0 - wall_thickness / 2.0, 0.0, 0.0),
                scale: Vec3::new(wall_thickness, bounds.y, 1.0),
                ..default()
            },
            sprite: Sprite { color: WALL_COLOR, ..default() },
            ..default()
        },
        WallLocation::Right,
        Collider { size: Vec2::new(wall_thickness, bounds.y) },
    ));

    // 顶墙
    commands.spawn((
        SpriteBundle {
            transform: Transform {
                translation: Vec3::new(0.0, bounds.y / 2.0 - wall_thickness / 2.0, 0.0),
                scale: Vec3::new(bounds.x, wall_thickness, 1.0),
                ..default()
            },
            sprite: Sprite { color: WALL_COLOR, ..default() },
            ..default()
        },
        WallLocation::Top,
        Collider { size: Vec2::new(bounds.x, wall_thickness) },
    ));

    // 4. 生成砖块阵列 Bricks
    let total_brick_width = BRICK_COLS as f32 * BRICK_SIZE.x + (BRICK_COLS - 1) as f32 * BRICK_GAP.x;
    let start_x = -total_brick_width / 2.0 + BRICK_SIZE.x / 2.0;
    let start_y = BRICK_OFFSET_Y;

    for row in 0..BRICK_ROWS {
        for col in 0..BRICK_COLS {
            let brick_position = Vec2::new(
                start_x + col as f32 * (BRICK_SIZE.x + BRICK_GAP.x),
                start_y + row as f32 * (BRICK_SIZE.y + BRICK_GAP.y),
            );

            let row_color = BRICK_COLORS[row % BRICK_COLORS.len()];
            let points = ((BRICK_ROWS - row) * 10) as u32;

            commands.spawn((
                SpriteBundle {
                    transform: Transform {
                        translation: brick_position.extend(0.0),
                        scale: Vec3::new(BRICK_SIZE.x, BRICK_SIZE.y, 1.0),
                        ..default()
                    },
                    sprite: Sprite {
                        color: row_color,
                        ..default()
                    },
                    ..default()
                },
                Brick { points },
                Collider { size: BRICK_SIZE },
            ));
        }
    }

    // 5. 生成得分 UI
    commands.spawn((
        TextBundle::from_sections([
            TextSection::new(
                "SCORE: ",
                TextStyle {
                    font: default(),
                    font_size: 30.0,
                    color: Color::WHITE,
                },
            ),
            TextSection::new(
                "0",
                TextStyle {
                    font: default(),
                    font_size: 30.0,
                    color: BALL_COLOR,
                },
            ),
        ])
        .with_style(Style {
            position_type: PositionType::Absolute,
            top: Val::Px(15.0),
            left: Val::Px(30.0),
            ..default()
        }),
        ScoreText,
    ));
}

// 移动挡板系统
fn move_paddle(
    keyboard_input: Res<ButtonInput<KeyCode>>,
    mut query: Query<(&mut Transform, &Collider), With<Paddle>>,
    time: Res<Time>,
) {
    let (mut paddle_transform, paddle_collider) = query.single_mut();
    let mut direction = 0.0;

    if keyboard_input.pressed(KeyCode::KeyA) || keyboard_input.pressed(KeyCode::ArrowLeft) {
        direction -= 1.0;
    }
    if keyboard_input.pressed(KeyCode::KeyD) || keyboard_input.pressed(KeyCode::ArrowRight) {
        direction += 1.0;
    }

    let new_x = paddle_transform.translation.x + direction * PADDLE_SPEED * time.delta_seconds();
    let left_bound = -SCREEN_WIDTH / 2.0 + paddle_collider.size.x / 2.0 + 20.0;
    let right_bound = SCREEN_WIDTH / 2.0 - paddle_collider.size.x / 2.0 - 20.0;

    paddle_transform.translation.x = new_x.clamp(left_bound, right_bound);
}

// 移动球系统
fn apply_velocity(mut query: Query<(&mut Transform, &Velocity), With<Ball>>, time: Res<Time>) {
    for (mut transform, velocity) in &mut query {
        transform.translation += velocity.extend(0.0) * time.delta_seconds();
    }
}

// 碰撞检测辅助方法
fn collide_aabb(pos_a: Vec2, size_a: Vec2, pos_b: Vec2, size_b: Vec2) -> Option<Collision> {
    let half_a = size_a / 2.0;
    let half_b = size_b / 2.0;

    let min_a = pos_a - half_a;
    let max_a = pos_a + half_a;
    let min_b = pos_b - half_b;
    let max_b = pos_b + half_b;

    if max_a.x < min_b.x || min_a.x > max_b.x || max_a.y < min_b.y || min_a.y > max_b.y {
        return None;
    }

    let overlap_x = (max_a.x.min(max_b.x) - min_a.x.max(min_b.x)).abs();
    let overlap_y = (max_a.y.min(max_b.y) - min_a.y.max(min_b.y)).abs();

    if overlap_x < overlap_y {
        if pos_a.x < pos_b.x {
            Some(Collision::Left)
        } else {
            Some(Collision::Right)
        }
    } else {
        if pos_a.y < pos_b.y {
            Some(Collision::Bottom)
        } else {
            Some(Collision::Top)
        }
    }
}

// 球体碰撞处理系统
fn check_ball_collisions(
    mut commands: Commands,
    mut scoreboard: ResMut<Scoreboard>,
    mut ball_query: Query<(&mut Transform, &mut Velocity, &Collider), With<Ball>>,
    paddle_query: Query<(&Transform, &Collider), (With<Paddle>, Without<Ball>)>,
    brick_query: Query<(Entity, &Transform, &Collider, &Brick), Without<Ball>>,
    wall_query: Query<(&Transform, &Collider), (With<WallLocation>, Without<Ball>)>,
) {
    for (mut ball_transform, mut ball_velocity, ball_collider) in &mut ball_query {
        let ball_pos = ball_transform.translation.truncate();
        let ball_size = ball_collider.size;

        // 1. 检查掉落到底板下方 (Reset ball)
        if ball_transform.translation.y < -SCREEN_HEIGHT / 2.0 {
            ball_transform.translation = Vec3::new(0.0, PADDLE_Y + 30.0, 1.0);
            let dir = BALL_INITIAL_DIRECTION.normalize();
            ball_velocity.0 = dir * BALL_INITIAL_SPEED;
            continue;
        }

        // 2. 挡板碰撞
        for (paddle_transform, paddle_collider) in &paddle_query {
            let paddle_pos = paddle_transform.translation.truncate();
            if let Some(_) = collide_aabb(ball_pos, ball_size, paddle_pos, paddle_collider.size) {
                // 如果在挡板上方，根据击中点与中心距离计算反弹角
                if ball_pos.y > paddle_pos.y {
                    let offset = (ball_pos.x - paddle_pos.x) / (paddle_collider.size.x / 2.0);
                    let clamp_offset = offset.clamp(-0.95, 0.95);
                    
                    let speed = ball_velocity.length();
                    // 动态调整反弹方向: clamp_offset 影响 x 轴速度方向
                    let new_dir = Vec2::new(clamp_offset * 0.8, 1.0).normalize();
                    ball_velocity.0 = new_dir * speed;
                }
            }
        }

        // 3. 墙壁碰撞
        for (wall_transform, wall_collider) in &wall_query {
            let wall_pos = wall_transform.translation.truncate();
            if let Some(collision) = collide_aabb(ball_pos, ball_size, wall_pos, wall_collider.size) {
                match collision {
                    Collision::Left | Collision::Right => ball_velocity.x = -ball_velocity.x,
                    Collision::Top | Collision::Bottom => ball_velocity.y = -ball_velocity.y,
                }
            }
        }

        // 4. 砖块碰撞
        for (brick_entity, brick_transform, brick_collider, brick) in &brick_query {
            let brick_pos = brick_transform.translation.truncate();
            if let Some(collision) = collide_aabb(ball_pos, ball_size, brick_pos, brick_collider.size) {
                // 反弹
                match collision {
                    Collision::Left | Collision::Right => ball_velocity.x = -ball_velocity.x,
                    Collision::Top | Collision::Bottom => ball_velocity.y = -ball_velocity.y,
                }

                // 增加得分
                scoreboard.score += brick.points;

                // 销毁砖块
                commands.entity(brick_entity).despawn();

                // 一次击中一块砖块后即中断砖块循环，避免帧内多次碰撞
                break;
            }
        }
    }
}

// 更新得分板系统
fn update_scoreboard(scoreboard: Res<Scoreboard>, mut query: Query<&mut Text, With<ScoreText>>) {
    if scoreboard.is_changed() {
        for mut text in &mut query {
            text.sections[1].value = scoreboard.score.to_string();
        }
    }
}
