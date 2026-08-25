<template>
  <div class="local-clock-container animate-fade-in" :class="{ 'zen-fullscreen': isZenMode, 'is-fullscreen': isFullscreen }">
    <!-- Header Control Toolbar (Hidden in Zen Mode) -->
    <div v-if="!isZenMode" class="clock-toolbar">
      <div class="toolbar-left">
        <div class="page-title">
          <Clock :size="22" class="icon-primary" />
          <h2>本地高精度时钟</h2>
        </div>
        <span class="title-subtext">实时本地时间、时区与天文农历看板</span>
      </div>

      <!-- Feature Controls: Visual Mode (Analog / Digital), Seconds, Milliseconds, 12/24H, Zen Mode -->
      <div class="toolbar-right">
        <!-- Mode Selection Dropdown -->
        <div class="mode-dropdown-container" ref="modeDropdownRef">
          <button
            class="mode-dropdown-trigger"
            @click="isModeDropdownOpen = !isModeDropdownOpen"
            title="选择时钟视觉风格"
          >
            <component :is="currentModeOption.icon" :size="15" class="mode-icon" />
            <span class="mode-name">{{ currentModeOption.name }}</span>
            <ChevronDown :size="13" class="mode-chevron" :class="{ rotated: isModeDropdownOpen }" />
          </button>

          <!-- Floating Dropdown Menu -->
          <div v-if="isModeDropdownOpen" class="mode-dropdown-menu animate-fade-in">
            <div class="dropdown-header">时钟视觉风格</div>
            <button
              v-for="opt in modeOptions"
              :key="opt.id"
              class="dropdown-mode-item"
              :class="{ active: displayMode === opt.id }"
              @click="selectMode(opt.id)"
            >
              <div class="item-icon-box">
                <component :is="opt.icon" :size="16" />
              </div>
              <div class="item-text-group">
                <span class="item-title">{{ opt.name }}</span>
                <span class="item-desc">{{ opt.desc }}</span>
              </div>
              <Check v-if="displayMode === opt.id" :size="15" class="item-check-icon" />
            </button>
          </div>
        </div>

        <button
          class="control-btn"
          :class="{ active: showSeconds }"
          @click="toggleSeconds"
          title="切换是否显示秒"
        >
          <Zap :size="14" />
          <span>秒 ({{ showSeconds ? '开' : '关' }})</span>
        </button>

        <button
          class="control-btn"
          :class="{ active: showMilliseconds }"
          @click="toggleMilliseconds"
          title="切换是否显示毫秒"
        >
          <Activity :size="14" />
          <span>毫秒 ({{ showMilliseconds ? '开' : '关' }})</span>
        </button>

        <button
          class="control-btn"
          :class="{ active: use12Hour }"
          @click="toggle12Hour"
          title="切换12小时制/24小时制"
        >
          <Clock :size="14" />
          <span>{{ use12Hour ? '12小时制' : '24小时制' }}</span>
        </button>

        <!-- Fullscreen Button -->
        <button
          class="control-btn btn-fullscreen"
          :class="{ active: isFullscreen }"
          @click="toggleFullscreen"
          :title="isFullscreen ? '退出全屏显示 (ESC)' : '进入全屏大屏时钟 (F11)'"
        >
          <Minimize v-if="isFullscreen" :size="14" />
          <Maximize v-else :size="14" />
          <span>{{ isFullscreen ? '退出全屏' : '全屏显示' }}</span>
        </button>

        <!-- Zen Fullscreen Immersion Button -->
        <button class="control-btn btn-zen" @click="isZenMode = true" title="进入全屏沉浸大钟模式">
          <Maximize2 :size="14" />
          <span>沉浸模式</span>
        </button>
      </div>
    </div>

    <!-- Exit Zen Mode Floating Actions -->
    <div v-if="isZenMode" class="zen-floating-actions">
      <button class="btn-exit-zen" @click="toggleFullscreen" :title="isFullscreen ? '退出全屏' : '全屏显示'">
        <Minimize v-if="isFullscreen" :size="15" />
        <Maximize v-else :size="15" />
        <span>{{ isFullscreen ? '退出全屏' : '全屏' }}</span>
      </button>
      <button class="btn-exit-zen btn-exit-zen-primary" @click="isZenMode = false" title="退出沉浸模式 (ESC)">
        <Minimize2 :size="15" />
        <span>退出沉浸</span>
      </button>
    </div>

    <!-- Main Clock Stage Area (左右两栏布局) -->
    <div class="clock-stage-wrapper">
      <div class="clock-split-container">
        <!-- Ambient Breathing Glow -->
        <div class="clock-ambient-glow"></div>

        <!-- Left Column: 时钟核心展示区 -->
        <div class="clock-col-left">
          <!-- 1. Analog Clock View -->
          <div v-if="displayMode === 'analog'" class="analog-clock-wrapper animate-fade-in">
            <svg class="analog-clock-svg" viewBox="0 0 280 280">
              <defs>
                <linearGradient id="bezelGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="rgba(255,255,255,0.4)" />
                  <stop offset="50%" stop-color="rgba(99,102,241,0.2)" />
                  <stop offset="100%" stop-color="rgba(15,23,42,0.3)" />
                </linearGradient>
                <filter id="handShadow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="3" stdDeviation="3" flood-opacity="0.35" />
                </filter>
              </defs>

              <!-- Outer Bezel & Dial Background -->
              <circle cx="140" cy="140" r="134" class="clock-outer-bezel" fill="url(#bezelGrad)" />
              <circle cx="140" cy="140" r="126" class="clock-dial-bg" />

              <!-- Ticks -->
              <g class="clock-ticks">
                <line
                  v-for="n in 60"
                  :key="'m' + n"
                  x1="140"
                  y1="20"
                  x2="140"
                  y2="26"
                  :transform="`rotate(${n * 6} 140 140)`"
                  class="minute-tick"
                />
                <line
                  v-for="n in 12"
                  :key="'h' + n"
                  x1="140"
                  y1="18"
                  x2="140"
                  y2="30"
                  :transform="`rotate(${n * 30} 140 140)`"
                  class="hour-tick"
                />
              </g>

              <!-- 12 Hours Numbers -->
              <text x="140" y="52" class="clock-number" text-anchor="middle">12</text>
              <text x="230" y="146" class="clock-number" text-anchor="middle">3</text>
              <text x="140" y="240" class="clock-number" text-anchor="middle">6</text>
              <text x="50" y="146" class="clock-number" text-anchor="middle">9</text>

              <!-- Hour Hand (时针) -->
              <g :transform="`rotate(${analogAngles.hour}, 140, 140)`">
                <line x1="140" y1="152" x2="140" y2="76" class="hand hour-hand" />
                <circle cx="140" cy="76" r="3.5" class="hour-tip" />
              </g>

              <!-- Minute Hand (分针) -->
              <g :transform="`rotate(${analogAngles.minute}, 140, 140)`">
                <line x1="140" y1="156" x2="140" y2="48" class="hand minute-hand" />
                <circle cx="140" cy="48" r="2.5" class="minute-tip" />
              </g>

              <!-- Second Hand (秒针) -->
              <g v-if="showSeconds" :transform="`rotate(${analogAngles.second}, 140, 140)`">
                <line x1="140" y1="165" x2="140" y2="32" class="hand second-hand" />
                <circle cx="140" cy="165" r="4.5" class="second-tail" />
              </g>

              <!-- Center Hub / Cap -->
              <circle cx="140" cy="140" r="7.5" class="center-pin-base" />
              <circle cx="140" cy="140" r="5" class="center-pin" />
              <circle cx="140" cy="140" r="2.5" class="center-jewel" />
            </svg>
          </div>

          <!-- 2. Digital Clock View -->
          <div v-else-if="displayMode === 'digital'" class="digital-clock-wrapper animate-fade-in">
            <div class="hero-digital-time">
              <div class="digits-group">
                <span class="digit-hours">{{ formattedLocalTime.hours }}</span>
                <span class="digit-colon">:</span>
                <span class="digit-minutes">{{ formattedLocalTime.minutes }}</span>
                <span v-if="showSeconds" class="digit-colon">:</span>
                <span v-if="showSeconds" class="digit-seconds">{{ formattedLocalTime.seconds }}</span>
                <span v-if="showMilliseconds" class="digit-milliseconds">.{{ formattedLocalTime.milliseconds }}</span>
              </div>
              <span v-if="use12Hour" class="digit-ampm">{{ formattedLocalTime.ampm }}</span>
            </div>
          </div>

          <!-- 3. Flip Clock View (经典 Fliqlo 拟真机械翻页时钟) -->
          <div v-else-if="displayMode === 'flip'" class="flip-clock-wrapper animate-fade-in">
            <div class="flip-clock-stage" :class="{ 'has-seconds': showSeconds }">
              <!-- Hours Flip Card -->
              <div class="flip-card-unit" :class="{ 'is-flipping': hoursFlip.flipping }">
                <!-- Static Background Upper (Shows target/current value) -->
                <div class="flip-half flip-upper flip-back-card">
                  <span class="flip-num">{{ hoursFlip.current }}</span>
                </div>
                <!-- Static Background Lower (Shows previous value until covered) -->
                <div class="flip-half flip-lower flip-back-card">
                  <span class="flip-num">{{ hoursFlip.previous }}</span>
                </div>

                <!-- Active 3D Animated Flaps (Rendered only when flipping) -->
                <template v-if="hoursFlip.flipping">
                  <div class="flip-half flip-upper flap-falling">
                    <span class="flip-num">{{ hoursFlip.previous }}</span>
                  </div>
                  <div class="flip-half flip-lower flap-unfolding">
                    <span class="flip-num">{{ hoursFlip.current }}</span>
                  </div>
                </template>

                <!-- Divider & Hinge Details -->
                <div class="flip-divider-line"></div>
                <div class="flip-hinge-pin flip-pin-left"></div>
                <div class="flip-hinge-pin flip-pin-right"></div>
                <span v-if="use12Hour" class="flip-ampm-tag">{{ formattedLocalTime.ampm }}</span>
              </div>

              <!-- Minutes Flip Card -->
              <div class="flip-card-unit" :class="{ 'is-flipping': minutesFlip.flipping }">
                <!-- Static Background Upper -->
                <div class="flip-half flip-upper flip-back-card">
                  <span class="flip-num">{{ minutesFlip.current }}</span>
                </div>
                <!-- Static Background Lower -->
                <div class="flip-half flip-lower flip-back-card">
                  <span class="flip-num">{{ minutesFlip.previous }}</span>
                </div>

                <!-- Active 3D Animated Flaps -->
                <template v-if="minutesFlip.flipping">
                  <div class="flip-half flip-upper flap-falling">
                    <span class="flip-num">{{ minutesFlip.previous }}</span>
                  </div>
                  <div class="flip-half flip-lower flap-unfolding">
                    <span class="flip-num">{{ minutesFlip.current }}</span>
                  </div>
                </template>

                <!-- Divider & Hinge Details -->
                <div class="flip-divider-line"></div>
                <div class="flip-hinge-pin flip-pin-left"></div>
                <div class="flip-hinge-pin flip-pin-right"></div>
              </div>

              <!-- Seconds Flip Card (Identical in size to Hours & Minutes) -->
              <template v-if="showSeconds">
                <div class="flip-card-unit" :class="{ 'is-flipping': secondsFlip.flipping }">
                  <!-- Static Background Upper -->
                  <div class="flip-half flip-upper flip-back-card">
                    <span class="flip-num">{{ secondsFlip.current }}</span>
                  </div>
                  <!-- Static Background Lower -->
                  <div class="flip-half flip-lower flip-back-card">
                    <span class="flip-num">{{ secondsFlip.previous }}</span>
                  </div>

                  <!-- Active 3D Animated Flaps -->
                  <template v-if="secondsFlip.flipping">
                    <div class="flip-half flip-upper flap-falling">
                      <span class="flip-num">{{ secondsFlip.previous }}</span>
                    </div>
                    <div class="flip-half flip-lower flap-unfolding">
                      <span class="flip-num">{{ secondsFlip.current }}</span>
                    </div>
                  </template>

                  <!-- Divider & Hinge Details -->
                  <div class="flip-divider-line"></div>
                  <div class="flip-hinge-pin flip-pin-left"></div>
                  <div class="flip-hinge-pin flip-pin-right"></div>
                </div>
              </template>
            </div>
          </div>

          <!-- 4. Nixie Vacuum Tube Clock View (复古辉光管时钟) -->
          <div v-else-if="displayMode === 'nixie'" class="nixie-stage animate-fade-in">
            <div class="nixie-board">
              <!-- Hours Tubes -->
              <div class="nixie-tube">
                <div class="nixie-mesh"></div>
                <div class="nixie-digit">{{ formattedLocalTime.hours[0] }}</div>
                <div class="nixie-glass-glare"></div>
              </div>
              <div class="nixie-tube">
                <div class="nixie-mesh"></div>
                <div class="nixie-digit">{{ formattedLocalTime.hours[1] }}</div>
                <div class="nixie-glass-glare"></div>
              </div>

              <!-- Colon Bulb -->
              <div class="nixie-dot-bulb">
                <span class="nixie-dot-light"></span>
                <span class="nixie-dot-light"></span>
              </div>

              <!-- Minutes Tubes -->
              <div class="nixie-tube">
                <div class="nixie-mesh"></div>
                <div class="nixie-digit">{{ formattedLocalTime.minutes[0] }}</div>
                <div class="nixie-glass-glare"></div>
              </div>
              <div class="nixie-tube">
                <div class="nixie-mesh"></div>
                <div class="nixie-digit">{{ formattedLocalTime.minutes[1] }}</div>
                <div class="nixie-glass-glare"></div>
              </div>

              <!-- Seconds Tubes (Optional) -->
              <template v-if="showSeconds">
                <div class="nixie-dot-bulb">
                  <span class="nixie-dot-light"></span>
                  <span class="nixie-dot-light"></span>
                </div>

                <div class="nixie-tube nixie-sec-tube">
                  <div class="nixie-mesh"></div>
                  <div class="nixie-digit">{{ formattedLocalTime.seconds[0] }}</div>
                  <div class="nixie-glass-glare"></div>
                </div>
                <div class="nixie-tube nixie-sec-tube">
                  <div class="nixie-mesh"></div>
                  <div class="nixie-digit">{{ formattedLocalTime.seconds[1] }}</div>
                  <div class="nixie-glass-glare"></div>
                </div>
              </template>
            </div>
          </div>

          <!-- 5. Concentric Rings View (同心轨迹环时钟) -->
          <div v-else-if="displayMode === 'rings'" class="rings-stage animate-fade-in">
            <svg class="rings-svg" viewBox="0 0 280 280">
              <defs>
                <linearGradient id="ringHourGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#3b82f6" />
                  <stop offset="100%" stop-color="#6366f1" />
                </linearGradient>
                <linearGradient id="ringMinGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#8b5cf6" />
                  <stop offset="100%" stop-color="#ec4899" />
                </linearGradient>
                <linearGradient id="ringSecGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stop-color="#10b981" />
                  <stop offset="100%" stop-color="#06b6d4" />
                </linearGradient>
              </defs>

              <!-- Track Backgrounds -->
              <circle cx="140" cy="140" r="114" class="ring-track ring-track-sec" />
              <circle cx="140" cy="140" r="90" class="ring-track ring-track-min" />
              <circle cx="140" cy="140" r="66" class="ring-track ring-track-hour" />

              <!-- Active Progress Rings -->
              <!-- Seconds Ring (r=114, circum=716.28) -->
              <circle
                v-if="showSeconds"
                cx="140"
                cy="140"
                r="114"
                class="ring-progress"
                stroke="url(#ringSecGrad)"
                stroke-dasharray="716.28"
                :stroke-dashoffset="ringOffsets.second"
                transform="rotate(-90 140 140)"
              />
              <!-- Minutes Ring (r=90, circum=565.48) -->
              <circle
                cx="140"
                cy="140"
                r="90"
                class="ring-progress"
                stroke="url(#ringMinGrad)"
                stroke-dasharray="565.48"
                :stroke-dashoffset="ringOffsets.minute"
                transform="rotate(-90 140 140)"
              />
              <!-- Hours Ring (r=66, circum=414.69) -->
              <circle
                cx="140"
                cy="140"
                r="66"
                class="ring-progress"
                stroke="url(#ringHourGrad)"
                stroke-dasharray="414.69"
                :stroke-dashoffset="ringOffsets.hour"
                transform="rotate(-90 140 140)"
              />

              <!-- Center Digital Readout -->
              <text x="140" y="136" class="ring-center-time" text-anchor="middle">
                {{ formattedLocalTime.hours }}:{{ formattedLocalTime.minutes }}
              </text>
              <text v-if="showSeconds" x="140" y="156" class="ring-center-sec" text-anchor="middle">
                :{{ formattedLocalTime.seconds }}
              </text>
            </svg>
          </div>

          <!-- 6. 7-Segment LED Display (复古数码管) -->
          <div v-else-if="displayMode === 'seven-segment'" class="seven-segment-stage animate-fade-in">
            <div class="seven-segment-board">
              <!-- Hours -->
              <div class="seg-digit-box">
                <span v-for="seg in ['a','b','c','d','e','f','g']" :key="seg" :class="['seg-bar', `seg-${seg}`, { on: isSegmentOn(formattedLocalTime.hours[0], seg) }]"></span>
              </div>
              <div class="seg-digit-box">
                <span v-for="seg in ['a','b','c','d','e','f','g']" :key="seg" :class="['seg-bar', `seg-${seg}`, { on: isSegmentOn(formattedLocalTime.hours[1], seg) }]"></span>
              </div>

              <!-- Colon -->
              <div class="seg-colon-box">
                <span class="seg-dot"></span>
                <span class="seg-dot"></span>
              </div>

              <!-- Minutes -->
              <div class="seg-digit-box">
                <span v-for="seg in ['a','b','c','d','e','f','g']" :key="seg" :class="['seg-bar', `seg-${seg}`, { on: isSegmentOn(formattedLocalTime.minutes[0], seg) }]"></span>
              </div>
              <div class="seg-digit-box">
                <span v-for="seg in ['a','b','c','d','e','f','g']" :key="seg" :class="['seg-bar', `seg-${seg}`, { on: isSegmentOn(formattedLocalTime.minutes[1], seg) }]"></span>
              </div>

              <!-- Seconds (Optional) -->
              <template v-if="showSeconds">
                <div class="seg-colon-box">
                  <span class="seg-dot"></span>
                  <span class="seg-dot"></span>
                </div>

                <div class="seg-digit-box seg-sec-digit">
                  <span v-for="seg in ['a','b','c','d','e','f','g']" :key="seg" :class="['seg-bar', `seg-${seg}`, { on: isSegmentOn(formattedLocalTime.seconds[0], seg) }]"></span>
                </div>
                <div class="seg-digit-box seg-sec-digit">
                  <span v-for="seg in ['a','b','c','d','e','f','g']" :key="seg" :class="['seg-bar', `seg-${seg}`, { on: isSegmentOn(formattedLocalTime.seconds[1], seg) }]"></span>
                </div>
              </template>
            </div>
          </div>

          <!-- 7. Chinese Word Grid Matrix (极简时间字阵) -->
          <div v-else-if="displayMode === 'matrix-words'" class="matrix-words-stage animate-fade-in">
            <div class="words-grid-card">
              <div v-for="(row, rIdx) in chineseWordRows" :key="rIdx" class="words-row">
                <span
                  v-for="(char, cIdx) in row"
                  :key="cIdx"
                  class="word-cell"
                  :class="{ active: isCharActive(char, rIdx, cIdx) }"
                >
                  {{ char }}
                </span>
              </div>
            </div>
          </div>

          <!-- 8. Bagua Chrono Compass (八卦时辰天体罗盘时钟) -->
          <div v-else-if="displayMode === 'compass'" class="bagua-compass-stage animate-fade-in">
            <svg class="compass-svg" viewBox="0 0 540 540">
              <defs>
                <radialGradient id="compassCenterGlow" cx="50%" cy="50%" r="50%">
                  <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.35" />
                  <stop offset="60%" stop-color="#18181b" stop-opacity="0.95" />
                  <stop offset="100%" stop-color="#09090b" stop-opacity="1" />
                </radialGradient>
                <linearGradient id="activeBeamGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stop-color="#f59e0b" stop-opacity="0.05" />
                  <stop offset="60%" stop-color="#fbbf24" stop-opacity="0.3" />
                  <stop offset="100%" stop-color="#fef08a" stop-opacity="0.85" />
                </linearGradient>
              </defs>

              <!-- Base Concentric Grid Rings -->
              <circle cx="270" cy="270" r="260" class="compass-ring-line outer-border" />
              <circle cx="270" cy="270" r="226" class="compass-ring-line" />
              <circle cx="270" cy="270" r="182" class="compass-ring-line" />
              <circle cx="270" cy="270" r="138" class="compass-ring-line" />
              <circle cx="270" cy="270" r="98" class="compass-ring-line" />
              <circle cx="270" cy="270" r="58" class="compass-ring-line" />

              <!-- Crosshairs Axis Lines -->
              <line x1="270" y1="10" x2="270" y2="530" class="compass-axis-line" />
              <line x1="10" y1="270" x2="530" y2="270" class="compass-axis-line" />

              <!-- Horizontal 3 o'clock Active Reading Beam -->
              <rect x="270" y="257" width="258" height="26" rx="4" class="compass-active-beam" />
              <polygon points="536,270 526,264 526,276" class="compass-pointer-head" />

              <!-- Ring 6: Seconds (r=243, 60 items) -->
              <g class="compass-ring-group sec-ring" :transform="`rotate(${compassRotations.secDeg} 270 270)`">
                <g v-for="(item, i) in compassSeconds" :key="'sec-' + i" :transform="`rotate(${i * 6} 270 270)`">
                  <text
                    x="513"
                    y="273"
                    text-anchor="end"
                    class="compass-text sec-text"
                    :class="{ active: i === compassRotations.currentSecIdx }"
                  >
                    {{ item }}
                  </text>
                </g>
              </g>

              <!-- Ring 5: Minutes (r=202, 60 items) -->
              <g class="compass-ring-group min-ring" :transform="`rotate(${compassRotations.minDeg} 270 270)`">
                <g v-for="(item, i) in compassMinutes" :key="'min-' + i" :transform="`rotate(${i * 6} 270 270)`">
                  <text
                    x="472"
                    y="273"
                    text-anchor="end"
                    class="compass-text min-text"
                    :class="{ active: i === compassRotations.currentMinIdx }"
                  >
                    {{ item }}
                  </text>
                </g>
              </g>

              <!-- Ring 4: ShiChen + Bagua Trigram (r=160, 12 items) -->
              <g class="compass-ring-group shichen-ring" :transform="`rotate(${compassRotations.shichenDeg} 270 270)`">
                <g v-for="(item, i) in compassShiChen" :key="'shichen-' + i" :transform="`rotate(${i * 30} 270 270)`">
                  <text
                    x="430"
                    y="273.5"
                    text-anchor="end"
                    class="compass-text shichen-text"
                    :class="{ active: i === compassRotations.currentShichenIdx }"
                  >
                    {{ item.name }} {{ item.gua }}
                  </text>
                </g>
              </g>

              <!-- Ring 3: Days (r=118, 31 items) -->
              <g class="compass-ring-group day-ring" :transform="`rotate(${compassRotations.dayDeg} 270 270)`">
                <g v-for="(item, i) in compassDays" :key="'day-' + i" :transform="`rotate(${i * (360 / 31)} 270 270)`">
                  <text
                    x="388"
                    y="273.5"
                    text-anchor="end"
                    class="compass-text day-text"
                    :class="{ active: i === compassRotations.currentDayIdx }"
                  >
                    {{ item }}
                  </text>
                </g>
              </g>

              <!-- Ring 2: Months (r=78, 12 items) -->
              <g class="compass-ring-group month-ring" :transform="`rotate(${compassRotations.monthDeg} 270 270)`">
                <g v-for="(item, i) in compassMonths" :key="'month-' + i" :transform="`rotate(${i * 30} 270 270)`">
                  <text
                    x="348"
                    y="274"
                    text-anchor="end"
                    class="compass-text month-text"
                    :class="{ active: i === compassRotations.currentMonthIdx }"
                  >
                    {{ item }}
                  </text>
                </g>
              </g>

              <!-- Ring 1: Central Core: Taiji Yin-Yang & Year (r=50) -->
              <circle cx="270" cy="270" r="50" class="compass-center-circle" fill="url(#compassCenterGlow)" />

              <!-- Taiji Rotating Graphic -->
              <g class="taiji-group" transform="translate(270, 270)">
                <circle cx="0" cy="0" r="22" fill="#09090b" stroke="#f59e0b" stroke-width="1.5" />
                <path d="M 0,-22 A 22,22 0 0,1 0,22 A 11,11 0 0,1 0,0 A 11,11 0 0,0 0,-22 Z" fill="#fbbf24" />
                <path d="M 0,22 A 22,22 0 0,1 0,-22 A 11,11 0 0,1 0,0 A 11,11 0 0,0 0,22 Z" fill="#18181b" />
                <circle cx="0" cy="-11" r="3.2" fill="#18181b" />
                <circle cx="0" cy="11" r="3.2" fill="#fbbf24" />
              </g>

              <!-- Year Text Badge -->
              <text x="270" y="306" text-anchor="middle" class="compass-year-badge">
                {{ compassYearText }}
              </text>
            </svg>
          </div>
        </div>

        <!-- Right Column: 日期、农历、时区与每日流逝看板 -->
        <div class="clock-col-right animate-fade-in">
          <!-- Timezone Status -->
          <div class="time-header-pill">
            <span class="pulse-indicator"></span>
            <span class="tz-label">{{ localTzName }}</span>
            <span class="tz-offset">{{ localOffsetStr }}</span>
          </div>

          <!-- Calendar & Lunar Information Cards -->
          <div class="calendar-detail-card">
            <div class="detail-pill date-pill">
              <Calendar :size="16" class="icon-accent" />
              <span>{{ formattedLocalTime.fullDateStr }}</span>
              <span class="weekday-tag">{{ formattedLocalTime.weekday }}</span>
            </div>
            <div class="detail-pill lunar-pill">
              <Sparkles :size="15" class="icon-lunar" />
              <span>{{ lunarText }}</span>
            </div>
          </div>

          <!-- Day Progress Section -->
          <div class="day-progress-section">
            <div class="progress-info-row">
              <span class="greeting-text">{{ greetingText }}</span>
              <span class="progress-percent">今日进度 {{ dayProgressPercent }}%</span>
            </div>
            <div class="day-progress-track">
              <div class="day-progress-bar" :style="{ width: `${dayProgressPercent}%` }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  Clock,
  Zap,
  Activity,
  Calendar,
  Tv,
  Disc,
  Layers,
  Flame,
  CircleDot,
  Hash,
  Type,
  Compass,
  ChevronDown,
  Check,
  Sparkles,
  Maximize,
  Minimize,
  Maximize2,
  Minimize2
} from 'lucide-vue-next'
import { getLunar } from '../../utils/lunar'

export type ClockVisualMode = 'analog' | 'digital' | 'flip' | 'nixie' | 'rings' | 'seven-segment' | 'matrix-words' | 'compass'

interface ModeOption {
  id: ClockVisualMode
  name: string
  desc: string
  icon: any
}

const modeOptions: ModeOption[] = [
  { id: 'analog', name: '模拟表盘', desc: '经典机械指针与高精刻度', icon: Disc },
  { id: 'digital', name: '数字大屏', desc: '现代等宽无衬线高精巨字', icon: Tv },
  { id: 'flip', name: '机械翻页', desc: '3D 拟真折叠翻牌动效', icon: Layers },
  { id: 'nixie', name: '复古辉光管', desc: '真空玻璃管金橙发光灯丝', icon: Flame },
  { id: 'rings', name: '同心轨迹环', desc: '三环时分秒流转科技光带', icon: CircleDot },
  { id: 'seven-segment', name: 'LED数码管', desc: '经典电子表发光段与暗纹', icon: Hash },
  { id: 'matrix-words', name: '时间字阵', desc: '极简汉字时序高亮矩阵', icon: Type },
  { id: 'compass', name: '八卦罗盘', desc: '天体同心六层旋转时辰罗盘', icon: Compass }
]

interface FlipUnitState {
  current: string
  previous: string
  flipping: boolean
  timerId?: any
}

const now = ref<Date>(new Date())
const showSeconds = ref<boolean>(true)
const showMilliseconds = ref<boolean>(false)
const use12Hour = ref<boolean>(false)
const displayMode = ref<ClockVisualMode>('analog')
const isZenMode = ref<boolean>(false)
const isFullscreen = ref<boolean>(false)

// Mode Dropdown State
const isModeDropdownOpen = ref<boolean>(false)
const modeDropdownRef = ref<HTMLElement | null>(null)

const currentModeOption = computed(() => {
  return modeOptions.find(o => o.id === displayMode.value) || modeOptions[0]
})

function selectMode(mode: ClockVisualMode) {
  displayMode.value = mode
  isModeDropdownOpen.value = false
  startClockLoop()
}

function handleDocumentClick(e: MouseEvent) {
  if (modeDropdownRef.value && !modeDropdownRef.value.contains(e.target as Node)) {
    isModeDropdownOpen.value = false
  }
}

// Flip Clock Unit States
const hoursFlip = ref<FlipUnitState>({ current: '00', previous: '00', flipping: false })
const minutesFlip = ref<FlipUnitState>({ current: '00', previous: '00', flipping: false })
const secondsFlip = ref<FlipUnitState>({ current: '00', previous: '00', flipping: false })

function triggerFlip(state: FlipUnitState, newVal: string) {
  if (state.current === newVal) return
  if (state.timerId) clearTimeout(state.timerId)
  state.previous = state.current
  state.current = newVal
  state.flipping = true
  state.timerId = setTimeout(() => {
    state.flipping = false
    state.previous = state.current
  }, 500)
}

let animationFrameId: number | null = null
let intervalTimerId: any = null

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => {})
    isFullscreen.value = true
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen().catch(() => {})
    }
    isFullscreen.value = false
  }
}

function handleFullscreenChange() {
  isFullscreen.value = !!document.fullscreenElement
}

function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (isModeDropdownOpen.value) isModeDropdownOpen.value = false
    if (isZenMode.value) isZenMode.value = false
  }
}

function updateTime() {
  now.value = new Date()
  if (showMilliseconds.value || displayMode.value === 'analog' || displayMode.value === 'rings') {
    animationFrameId = requestAnimationFrame(updateTime)
  }
}

function startClockLoop() {
  stopClockLoop()
  if (showMilliseconds.value || displayMode.value === 'analog' || displayMode.value === 'rings') {
    animationFrameId = requestAnimationFrame(updateTime)
  } else {
    intervalTimerId = setInterval(() => { now.value = new Date() }, 1000)
  }
}

function stopClockLoop() {
  if (animationFrameId !== null) { cancelAnimationFrame(animationFrameId); animationFrameId = null }
  if (intervalTimerId !== null) { clearInterval(intervalTimerId); intervalTimerId = null }
}

function toggleSeconds() { showSeconds.value = !showSeconds.value }
function toggleMilliseconds() { showMilliseconds.value = !showMilliseconds.value; startClockLoop() }
function toggle12Hour() { use12Hour.value = !use12Hour.value }

const localTzName = computed(() => Intl.DateTimeFormat().resolvedOptions().timeZone || 'Asia/Shanghai')
const localOffsetStr = computed(() => {
  const offset = -now.value.getTimezoneOffset()
  const sign = offset >= 0 ? '+' : '-'
  const abs = Math.abs(offset)
  return `UTC${sign}${String(Math.floor(abs/60)).padStart(2,'0')}:${String(abs%60).padStart(2,'0')}`
})

const formattedLocalTime = computed(() => {
  const d = now.value
  let h = d.getHours(), ampm = ''
  if (use12Hour.value) { ampm = h >= 12 ? 'PM' : 'AM'; h = h % 12 || 12 }
  return {
    hours: String(h).padStart(2, '0'),
    minutes: String(d.getMinutes()).padStart(2, '0'),
    seconds: String(d.getSeconds()).padStart(2, '0'),
    milliseconds: String(Math.floor(d.getMilliseconds() / 10)).padStart(2, '0'),
    ampm,
    weekday: ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'][d.getDay()],
    fullDateStr: `${d.getFullYear()}年${String(d.getMonth() + 1).padStart(2, '0')}月${String(d.getDate()).padStart(2, '0')}日`
  }
})

watch(() => formattedLocalTime.value.hours, (newVal) => {
  triggerFlip(hoursFlip.value, newVal)
}, { immediate: true })

watch(() => formattedLocalTime.value.minutes, (newVal) => {
  triggerFlip(minutesFlip.value, newVal)
}, { immediate: true })

watch(() => formattedLocalTime.value.seconds, (newVal) => {
  triggerFlip(secondsFlip.value, newVal)
}, { immediate: true })

const analogAngles = computed(() => {
  const d = now.value
  const ms = d.getMilliseconds()
  const sec = d.getSeconds() + (showMilliseconds.value || displayMode.value === 'analog' ? ms / 1000 : 0)
  const min = d.getMinutes() + sec / 60
  const hr = (d.getHours() % 12) + min / 60
  return {
    second: sec * 6,
    minute: min * 6,
    hour: hr * 30
  }
})

// 5. Concentric Rings Offsets Calculation
const ringOffsets = computed(() => {
  const d = now.value
  const sec = d.getSeconds() + d.getMilliseconds() / 1000
  const min = d.getMinutes() + sec / 60
  const hr = (d.getHours() % (use12Hour.value ? 12 : 24)) + min / 60
  const hrMax = use12Hour.value ? 12 : 24

  const secCircum = 716.28
  const minCircum = 565.48
  const hrCircum = 414.69

  return {
    second: secCircum - (sec / 60) * secCircum,
    minute: minCircum - (min / 60) * minCircum,
    hour: hrCircum - (hr / hrMax) * hrCircum
  }
})

// 6. 7-Segment LED Segment Mapping
const SEGMENT_MAP: Record<string, string[]> = {
  '0': ['a', 'b', 'c', 'd', 'e', 'f'],
  '1': ['b', 'c'],
  '2': ['a', 'b', 'd', 'e', 'g'],
  '3': ['a', 'b', 'c', 'd', 'g'],
  '4': ['b', 'c', 'f', 'g'],
  '5': ['a', 'c', 'd', 'f', 'g'],
  '6': ['a', 'c', 'd', 'e', 'f', 'g'],
  '7': ['a', 'b', 'c'],
  '8': ['a', 'b', 'c', 'd', 'e', 'f', 'g'],
  '9': ['a', 'b', 'c', 'd', 'f', 'g']
}

function isSegmentOn(digitStr: string, segment: string): boolean {
  return (SEGMENT_MAP[digitStr] || []).includes(segment)
}

// 7. Chinese Word Grid Matrix (10 x 6 规范汉字时钟点阵)
const chineseWordRows = [
  ['现', '在', '是', '早', '上', '中', '午', '下', '午', '晚'],
  ['上', '夜', '深', '凌', '晨', '一', '二', '三', '四', '五'],
  ['六', '七', '八', '九', '十', '一', '十', '二', '点', '整'],
  ['半', '一', '刻', '三', '刻', '零', '一', '二', '三', '四'],
  ['五', '十', '一', '二', '三', '四', '五', '六', '七', '八'],
  ['九', '分', '十', '二', '三', '四', '五', '十', '秒', '钟']
]

const activeChineseChars = computed(() => {
  const d = now.value
  const h = d.getHours()
  const m = d.getMinutes()
  const s = d.getSeconds()
  const activeSet = new Set<string>()

  // 1. 引导前缀 (始终点亮: "现在是")
  activeSet.add('0,0') // 现
  activeSet.add('0,1') // 在
  activeSet.add('0,2') // 是

  // 2. 时段语义映射 (早上/上午/中午/下午/晚上/夜深/凌晨)
  if (h >= 5 && h < 9) {
    activeSet.add('0,3'); activeSet.add('0,4') // 早上
  } else if (h >= 9 && h < 11.5) {
    activeSet.add('0,4'); activeSet.add('0,6') // 上午
  } else if (h >= 11.5 && h < 13) {
    activeSet.add('0,5'); activeSet.add('0,6') // 中午
  } else if (h >= 13 && h < 18) {
    activeSet.add('0,7'); activeSet.add('0,8') // 下午
  } else if (h >= 18 && h < 22) {
    activeSet.add('0,9'); activeSet.add('1,0') // 晚上
  } else if (h >= 22 || h < 1) {
    activeSet.add('1,1'); activeSet.add('1,2') // 夜深
  } else {
    activeSet.add('1,3'); activeSet.add('1,4') // 凌晨
  }

  // 3. 小时数映射 (1~12点)
  const hr12 = h % 12 || 12
  if (hr12 === 1) activeSet.add('1,5') // 一
  else if (hr12 === 2) activeSet.add('1,6') // 二
  else if (hr12 === 3) activeSet.add('1,7') // 三
  else if (hr12 === 4) activeSet.add('1,8') // 四
  else if (hr12 === 5) activeSet.add('1,9') // 五
  else if (hr12 === 6) activeSet.add('2,0') // 六
  else if (hr12 === 7) activeSet.add('2,1') // 七
  else if (hr12 === 8) activeSet.add('2,2') // 八
  else if (hr12 === 9) activeSet.add('2,3') // 九
  else if (hr12 === 10) activeSet.add('2,4') // 十
  else if (hr12 === 11) { activeSet.add('2,4'); activeSet.add('2,5') } // 十一
  else if (hr12 === 12) { activeSet.add('2,6'); activeSet.add('2,7') } // 十二
  activeSet.add('2,8') // 点

  // 辅助函数: 点亮数字 1~9 (排布在 Row 4 & Row 5)
  function addUnitChar(digit: number) {
    if (digit >= 1 && digit <= 8) {
      activeSet.add(`4,${1 + digit}`)
    } else if (digit === 9) {
      activeSet.add('5,0')
    }
  }

  // 4. 分钟数映射 (整/一刻/半/三刻/各分钟)
  if (m === 0) {
    activeSet.add('2,9') // 整
  } else if (m === 15) {
    activeSet.add('3,1'); activeSet.add('3,2') // 一刻
  } else if (m === 30) {
    activeSet.add('3,0') // 半
  } else if (m === 45) {
    activeSet.add('3,3'); activeSet.add('3,4') // 三刻
  } else {
    const mTens = Math.floor(m / 10)
    const mUnits = m % 10

    if (mTens === 0) {
      activeSet.add('3,5') // 零
      addUnitChar(mUnits)
    } else if (mTens === 1) {
      activeSet.add('4,1') // 十
      if (mUnits > 0) addUnitChar(mUnits)
    } else {
      if (mTens === 2) activeSet.add('3,7') // 二
      else if (mTens === 3) activeSet.add('3,8') // 三
      else if (mTens === 4) activeSet.add('3,9') // 四
      else if (mTens === 5) activeSet.add('4,0') // 五
      activeSet.add('4,1') // 十
      if (mUnits > 0) addUnitChar(mUnits)
    }
    activeSet.add('5,1') // 分
  }

  // 5. 实时秒数联动 (开启秒显示时联动高亮)
  if (showSeconds.value) {
    if (s === 0) {
      activeSet.add('5,8'); activeSet.add('5,9') // 秒钟
    } else {
      const sTens = Math.floor(s / 10)
      const sUnits = s % 10

      if (sTens === 0) {
        activeSet.add('3,5') // 零
        addUnitChar(sUnits)
      } else if (sTens === 1) {
        activeSet.add('5,2') // 十
        if (sUnits > 0) addUnitChar(sUnits)
      } else {
        if (sTens === 2) activeSet.add('5,3') // 二
        else if (sTens === 3) activeSet.add('5,4') // 三
        else if (sTens === 4) activeSet.add('5,5') // 四
        else if (sTens === 5) activeSet.add('5,6') // 五
        activeSet.add('5,7') // 十
        if (sUnits > 0) addUnitChar(sUnits)
      }
      activeSet.add('5,8') // 秒
    }
  }

  return activeSet
})

function isCharActive(_char: string, rIdx: number, cIdx: number): boolean {
  return activeChineseChars.value.has(`${rIdx},${cIdx}`)
}

// 8. Bagua Chrono Compass (八卦时辰天体罗盘时钟)
const compassMonths = ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月']
const compassDays = [
  '初一', '初二', '初三', '初四', '初五', '初六', '初七', '初八', '初九', '初十',
  '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
  '廿一', '廿二', '廿三', '廿四', '廿五', '廿六', '廿七', '廿八', '廿九', '三十', '卅一'
]
const compassShiChen = [
  { name: '子时', gua: '☵ 坎' },
  { name: '丑时', gua: '☶ 艮' },
  { name: '寅时', gua: '☶ 艮' },
  { name: '卯时', gua: '☳ 震' },
  { name: '辰时', gua: '☴ 巽' },
  { name: '巳时', gua: '☴ 巽' },
  { name: '午时', gua: '☲ 离' },
  { name: '未时', gua: '☷ 坤' },
  { name: '申时', gua: '☷ 坤' },
  { name: '酉时', gua: '☱ 兑' },
  { name: '戌时', gua: '☰ 乾' },
  { name: '亥时', gua: '☰ 乾' }
]
const compassMinutes = Array.from({ length: 60 }, (_, i) => `${i < 10 ? '0' + i : i}分`)
const compassSeconds = Array.from({ length: 60 }, (_, i) => `${i < 10 ? '0' + i : i}秒`)

const GAN_NAMES = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
const ZHI_NAMES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

const compassYearText = computed(() => {
  const y = now.value.getFullYear()
  const gan = GAN_NAMES[(y - 4 + 10000) % 10]
  const zhi = ZHI_NAMES[(y - 4 + 12000) % 12]
  return `${y} · ${gan}${zhi}`
})

const compassRotations = computed(() => {
  const d = now.value
  const s = d.getSeconds() + (showMilliseconds.value ? d.getMilliseconds() / 1000 : 0)
  const m = d.getMinutes() + s / 60
  const shichenIndex = Math.floor(((d.getHours() + 1) % 24) / 2)
  const day = d.getDate()
  const month = d.getMonth()

  return {
    secDeg: -(s * 6),
    minDeg: -(m * 6),
    shichenDeg: -(shichenIndex * 30 + (d.getMinutes() / 120) * 30),
    dayDeg: -((day - 1) * (360 / 31)),
    monthDeg: -(month * 30),
    currentMonthIdx: month,
    currentDayIdx: day - 1,
    currentShichenIdx: shichenIndex,
    currentMinIdx: d.getMinutes(),
    currentSecIdx: d.getSeconds()
  }
})

const lunarText = computed(() => {
  try {
    const l = getLunar(now.value)
    return l ? `农历 ${l.fullText}${l.solarTerm ? ' · ' + l.solarTerm : ''}` : '农历吉祥 · 岁月静好'
  } catch { return '农历吉祥 · 岁月静好' }
})

const greetingText = computed(() => {
  const h = now.value.getHours()
  if (h < 5) return '✨ 夜深了 · 早点休息'
  if (h < 9) return '🌅 晨光破晓 · 新的一天开启'
  if (h < 12) return '☀️ 早上好 · 保持专注与高效'
  if (h < 14) return '🍲 中午好 · 记得享用午餐'
  if (h < 18) return '☕ 下午好 · 专注投入收获满满'
  return '🌙 晚上好 · 享受惬意时光'
})

const dayProgressPercent = computed(() => (((now.value.getHours() * 3600 + now.value.getMinutes() * 60 + now.value.getSeconds()) / 86400) * 100).toFixed(1))

onMounted(() => {
  startClockLoop()
  window.addEventListener('keydown', handleKeyDown)
  document.addEventListener('click', handleDocumentClick)
  document.addEventListener('fullscreenchange', handleFullscreenChange)
})
onUnmounted(() => {
  stopClockLoop()
  window.removeEventListener('keydown', handleKeyDown)
  document.removeEventListener('click', handleDocumentClick)
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
})
</script>

<style scoped>
.local-clock-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  padding: 8px 16px;
  gap: 8px;
  box-sizing: border-box;
  overflow: hidden;
}

/* Zen Fullscreen Mode */
.local-clock-container.zen-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  padding: 0;
  z-index: 99999;
  background: var(--bg-app, #0f172a);
  display: flex;
  align-items: center;
  justify-content: center;
}

.zen-floating-actions {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 100000;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-exit-zen {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 20px;
  color: #ffffff;
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.btn-exit-zen:hover {
  background: var(--primary, #3b82f6);
  transform: translateY(-1px);
}

.btn-exit-zen-primary {
  background: rgba(59, 130, 246, 0.85);
  border-color: rgba(59, 130, 246, 0.4);
}

.btn-exit-zen-primary:hover {
  background: #2563eb;
}

/* Header Control Toolbar */
.clock-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.page-title h2 {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-main, #0f172a);
  margin: 0;
}

.icon-primary {
  color: var(--primary, #3b82f6);
}

.title-subtext {
  font-size: 12.5px;
  color: var(--text-muted, #64748b);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

/* Mode Selection Dropdown Styles */
.mode-dropdown-container {
  position: relative;
  z-index: 50;
}

.mode-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  color: var(--text-main, #0f172a);
  font-size: 12.5px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.03);
}

.mode-dropdown-trigger:hover {
  border-color: var(--primary, #3b82f6);
  background: rgba(59, 130, 246, 0.04);
}

.mode-icon {
  color: var(--primary, #3b82f6);
}

.mode-chevron {
  color: var(--text-muted, #94a3b8);
  transition: transform 0.2s ease;
}

.mode-chevron.rotated {
  transform: rotate(180deg);
}

.mode-dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  min-width: 220px;
  background: var(--bg-surface, #ffffff);
  backdrop-filter: blur(16px);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 14px;
  padding: 6px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 3px;
  z-index: 1000;
}

.dropdown-header {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-muted, #94a3b8);
  padding: 6px 10px 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.dropdown-mode-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  border-radius: 10px;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  width: 100%;
}

.dropdown-mode-item:hover {
  background: rgba(59, 130, 246, 0.08);
}

.dropdown-mode-item.active {
  background: rgba(59, 130, 246, 0.12);
}

.item-icon-box {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--primary, #3b82f6);
  flex-shrink: 0;
}

.dropdown-mode-item.active .item-icon-box {
  background: var(--primary, #3b82f6);
  color: #ffffff;
}

.item-text-group {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.item-title {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-main, #0f172a);
}

.item-desc {
  font-size: 11px;
  color: var(--text-muted, #64748b);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-check-icon {
  color: var(--primary, #3b82f6);
  flex-shrink: 0;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-surface, #ffffff);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 10px;
  color: var(--text-muted, #64748b);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.control-btn:hover {
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.control-btn.active {
  background: rgba(59, 130, 246, 0.08);
  border-color: var(--primary, #3b82f6);
  color: var(--primary, #3b82f6);
}

.btn-fullscreen {
  background: rgba(59, 130, 246, 0.08);
  border-color: rgba(59, 130, 246, 0.25);
  color: var(--primary, #3b82f6);
}

.btn-fullscreen:hover {
  background: var(--primary, #3b82f6);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.35);
}

.btn-zen {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(168, 85, 247, 0.1));
  border-color: rgba(99, 102, 241, 0.3);
  color: #6366f1;
}

.btn-zen:hover {
  background: linear-gradient(135deg, #6366f1, #a855f7);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.35);
}

/* Main Clock Showcase Stage (左右两栏高精度看板设计) */
.clock-stage-wrapper {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  padding: 0;
  overflow: hidden;
}

.zen-fullscreen .clock-stage-wrapper {
  width: 100%;
  height: 100%;
  padding: 0;
}

/* ============================================================
   Retro Mechanical 3D Flip Clock Styles (经典 Fliqlo 拟真翻页)
   ============================================================ */
.flip-clock-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.flip-clock-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(10px, 1.8vw, 22px);
  padding: 4px;
}

.flip-clock-stage.has-seconds {
  gap: clamp(6px, 1.2vw, 14px);
}

/* Standard 2-cards (Hours + Minutes) */
.flip-card-unit {
  position: relative;
  width: clamp(100px, 14vw, 148px);
  height: clamp(115px, 16vw, 170px);
  perspective: 600px;
  border-radius: 12px;
  box-shadow:
    0 14px 28px rgba(0, 0, 0, 0.35),
    0 4px 10px rgba(0, 0, 0, 0.22);
  user-select: none;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #18181c;
}

/* 3-cards: Hours + Minutes + Seconds (All 3 identical in size) */
.flip-clock-stage.has-seconds .flip-card-unit {
  width: clamp(78px, 10vw, 114px);
  height: clamp(94px, 12vw, 136px);
  border-radius: 10px;
}

.flip-half {
  position: absolute;
  left: 0;
  width: 100%;
  height: 50%;
  overflow: hidden;
  box-sizing: border-box;
  background: #1c1c22;
  color: #f8fafc;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.flip-upper {
  top: 0;
  border-top-left-radius: 12px;
  border-top-right-radius: 12px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.7);
  background: linear-gradient(180deg, #222228 0%, #1a1a20 100%);
}

.flip-clock-stage.has-seconds .flip-upper {
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
}

.flip-upper .flip-num {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 200%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(64px, 9vw, 98px);
  font-weight: 800;
  letter-spacing: -2px;
  color: #ffffff;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  line-height: 1;
}

.flip-clock-stage.has-seconds .flip-upper .flip-num {
  font-size: clamp(48px, 6.4vw, 76px);
  letter-spacing: -1.5px;
}

.flip-lower {
  bottom: 0;
  border-bottom-left-radius: 12px;
  border-bottom-right-radius: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: linear-gradient(180deg, #16161a 0%, #121215 100%);
}

.flip-clock-stage.has-seconds .flip-lower {
  border-bottom-left-radius: 10px;
  border-bottom-right-radius: 10px;
}

.flip-lower .flip-num {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 200%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(64px, 9vw, 98px);
  font-weight: 800;
  letter-spacing: -2px;
  color: #f1f5f9;
  text-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  line-height: 1;
}

.flip-clock-stage.has-seconds .flip-lower .flip-num {
  font-size: clamp(48px, 6.4vw, 76px);
  letter-spacing: -1.5px;
}

/* 3D Dynamic Flap Animations */
.flap-falling {
  transform-origin: bottom center;
  animation: flip-fall 0.25s cubic-bezier(0.37, 0, 0.63, 1) forwards;
  z-index: 5;
}

.flap-unfolding {
  transform-origin: top center;
  transform: rotateX(90deg);
  animation: flip-unfold 0.25s cubic-bezier(0.37, 0, 0.63, 1) 0.24s forwards;
  z-index: 6;
}

@keyframes flip-fall {
  0% {
    transform: rotateX(0deg);
  }
  100% {
    transform: rotateX(-90deg);
  }
}

@keyframes flip-unfold {
  0% {
    transform: rotateX(90deg);
  }
  100% {
    transform: rotateX(0deg);
  }
}

.flip-divider-line {
  position: absolute;
  top: calc(50% - 1px);
  left: 0;
  width: 100%;
  height: 2px;
  background: #09090b;
  z-index: 10;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.08);
}

.flip-hinge-pin {
  position: absolute;
  top: calc(50% - 5px);
  width: 4px;
  height: 10px;
  background: #3f3f46;
  border-radius: 2px;
  z-index: 12;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
}
.flip-pin-left { left: -2px; }
.flip-pin-right { right: -2px; }

.flip-ampm-tag {
  position: absolute;
  top: 8px;
  left: 10px;
  font-size: 11px;
  font-weight: 800;
  color: #a1a1aa;
  z-index: 15;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

/* 4. Retro Nixie Vacuum Tubes (复古辉光管) */
.nixie-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.nixie-board {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(4px, 0.8vw, 10px);
  padding: 10px 14px;
  background: #09090b;
  border-radius: 18px;
  border: 1px solid #27272a;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.8), 0 8px 24px rgba(0, 0, 0, 0.35);
}

.nixie-tube {
  position: relative;
  width: clamp(44px, 5.5vw, 68px);
  height: clamp(80px, 10.5vw, 128px);
  background: radial-gradient(circle at 50% 30%, rgba(255, 140, 0, 0.08) 0%, #0d0d11 75%);
  border: 1.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 30px 30px 8px 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.5), inset 0 0 12px rgba(255, 120, 0, 0.12);
}

.nixie-mesh {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: radial-gradient(rgba(255, 255, 255, 0.08) 1px, transparent 0);
  background-size: 4px 4px;
  pointer-events: none;
  opacity: 0.7;
}

.nixie-digit {
  font-family: 'Times New Roman', Times, serif, ui-monospace;
  font-size: clamp(42px, 5.8vw, 72px);
  font-weight: 900;
  color: #ff9900;
  text-shadow:
    0 0 4px #ffdd88,
    0 0 10px #ff8800,
    0 0 22px #ff4400,
    0 0 36px rgba(255, 50, 0, 0.75);
  z-index: 2;
  user-select: none;
  line-height: 1;
}

.nixie-glass-glare {
  position: absolute;
  top: 6px;
  left: 6px;
  width: 35%;
  height: 70%;
  border-left: 2px solid rgba(255, 255, 255, 0.4);
  border-top-left-radius: 20px;
  filter: blur(1px);
  pointer-events: none;
  z-index: 3;
}

.nixie-dot-bulb {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 0 2px;
}

.nixie-dot-light {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ffaa00;
  box-shadow: 0 0 8px #ff7700, 0 0 16px #ff3300;
  animation: blink 2s infinite;
}

/* 5. Concentric Rings Styles (同心轨迹环) */
.rings-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.rings-svg {
  width: min(230px, 32vh);
  height: min(230px, 32vh);
  filter: drop-shadow(0 10px 24px rgba(0, 0, 0, 0.12));
}

.ring-track {
  fill: none;
  stroke: var(--border-color, #e2e8f0);
  stroke-width: 12;
  opacity: 0.35;
}

.ring-progress {
  fill: none;
  stroke-width: 12;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.ring-center-time {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 32px;
  font-weight: 800;
  fill: var(--text-main, #0f172a);
}

.ring-center-sec {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 15px;
  font-weight: 700;
  fill: var(--primary, #6366f1);
}

/* 6. 7-Segment LED Display (复古数码管) */
.seven-segment-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.seven-segment-board {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: clamp(6px, 1vw, 12px);
  padding: 14px 18px;
  background: #09090b;
  border-radius: 18px;
  border: 1px solid #27272a;
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.7);
}

.seg-digit-box {
  position: relative;
  width: clamp(34px, 4.5vw, 54px);
  height: clamp(68px, 9vw, 108px);
}

.seg-bar {
  position: absolute;
  background: #064e3b;
  opacity: 0.12;
  border-radius: 3px;
  transition: all 0.15s ease;
}

.seg-bar.on {
  background: #10b981;
  opacity: 1;
  box-shadow: 0 0 10px #10b981, 0 0 20px rgba(16, 185, 129, 0.6);
}

.seg-a { top: 0; left: 4px; right: 4px; height: 6px; }
.seg-b { top: 4px; right: 0; width: 6px; height: calc(50% - 4px); }
.seg-c { bottom: 4px; right: 0; width: 6px; height: calc(50% - 4px); }
.seg-d { bottom: 0; left: 4px; right: 4px; height: 6px; }
.seg-e { bottom: 4px; left: 0; width: 6px; height: calc(50% - 4px); }
.seg-f { top: 4px; left: 0; width: 6px; height: calc(50% - 4px); }
.seg-g { top: calc(50% - 3px); left: 4px; right: 4px; height: 6px; }

.seg-colon-box {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 0 2px;
}

.seg-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: blink 2s infinite;
}

/* 7. Chinese Word Grid Matrix (极简时间字阵) */
.matrix-words-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.words-grid-card {
  display: flex;
  flex-direction: column;
  gap: clamp(4px, 0.8vw, 8px);
  padding: clamp(10px, 1.4vw, 16px) clamp(12px, 1.8vw, 20px);
  background: #09090b;
  border-radius: 18px;
  border: 1px solid #27272a;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.words-row {
  display: flex;
  gap: clamp(4px, 0.8vw, 8px);
  justify-content: space-between;
}

.word-cell {
  width: clamp(22px, 2.8vw, 34px);
  height: clamp(22px, 2.8vw, 34px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: clamp(12.5px, 1.5vw, 17px);
  font-weight: 700;
  color: #27272a;
  border-radius: 6px;
  transition: all 0.25s ease;
  user-select: none;
}

.word-cell.active {
  color: #22d3ee;
  text-shadow:
    0 0 8px #06b6d4,
    0 0 16px rgba(6, 182, 212, 0.7);
  background: rgba(6, 182, 212, 0.15);
  transform: scale(1.05);
  box-shadow: 0 0 12px rgba(6, 182, 212, 0.2);
}

/* 8. Bagua Chrono Compass (八卦时辰天体罗盘) */
.bagua-compass-stage {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.compass-svg {
  width: min(340px, 46vh);
  height: min(340px, 46vh);
  filter: drop-shadow(0 14px 36px rgba(0, 0, 0, 0.45));
  overflow: visible;
}

.compass-ring-line {
  fill: none;
  stroke: rgba(251, 191, 36, 0.15);
  stroke-width: 1;
}

.compass-ring-line.outer-border {
  stroke: rgba(251, 191, 36, 0.4);
  stroke-width: 1.5;
}

.compass-axis-line {
  stroke: rgba(251, 191, 36, 0.08);
  stroke-width: 1;
  stroke-dasharray: 4 4;
}

.compass-active-beam {
  fill: url(#activeBeamGrad);
  filter: drop-shadow(0 0 10px rgba(251, 191, 36, 0.3));
}

.compass-pointer-head {
  fill: #fbbf24;
  filter: drop-shadow(0 0 6px #f59e0b);
}

.compass-ring-group {
  transition: transform 0.25s cubic-bezier(0.2, 0, 0, 1);
}

.compass-ring-group.sec-ring {
  transition: transform 0.08s linear;
}

.compass-text {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  fill: #52525b;
  font-size: 8.5px;
  font-weight: 600;
  user-select: none;
  transition: fill 0.2s ease;
}

.sec-text {
  font-size: 8px;
}

.min-text {
  font-size: 8.5px;
}

.shichen-text {
  font-size: 9px;
  font-weight: 700;
}

.day-text {
  font-size: 8.5px;
}

.month-text {
  font-size: 9px;
  font-weight: 700;
}

.compass-text.active {
  fill: #fef08a;
  font-weight: 800;
  text-shadow: 0 0 8px rgba(251, 191, 36, 0.9);
}

.compass-center-circle {
  stroke: rgba(251, 191, 36, 0.3);
  stroke-width: 1.5;
}

.taiji-group {
  animation: taiji-slow-spin 60s linear infinite;
  transform-origin: 0 0;
}

@keyframes taiji-slow-spin {
  0% {
    transform: translate(270px, 270px) rotate(0deg);
  }
  100% {
    transform: translate(270px, 270px) rotate(360deg);
  }
}

.compass-year-badge {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", sans-serif;
  font-size: 10px;
  font-weight: 800;
  fill: #fbbf24;
  letter-spacing: 1px;
}

.clock-split-container {
  position: relative;
  width: 100%;
  max-width: 960px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 36px;
  box-sizing: border-box;
  padding: 8px 12px;
}

.clock-col-left {
  flex: 1.1;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.clock-col-right {
  flex: 0.9;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 14px;
  max-width: 420px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.calendar-detail-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: 100%;
}

.clock-ambient-glow {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 520px;
  height: 520px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.09) 0%, rgba(236, 72, 153, 0.03) 50%, transparent 70%);
  pointer-events: none;
  animation: pulse-glow 6s infinite ease-in-out;
}

@keyframes pulse-glow {
  0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 0.8; }
  50% { transform: translate(-50%, -50%) scale(1.18); opacity: 1; }
}

/* Analog Stage & SVG Hands */
.analog-clock-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.digital-clock-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.analog-clock-svg {
  width: min(210px, 30vh);
  height: min(210px, 30vh);
  filter: drop-shadow(0 10px 24px rgba(0, 0, 0, 0.12));
}

.clock-outer-bezel {
  stroke: var(--border-color, #cbd5e1);
  stroke-width: 2.5;
}

.clock-dial-bg {
  fill: var(--bg-surface, #ffffff);
  stroke: rgba(0, 0, 0, 0.04);
  stroke-width: 1;
}

.minute-tick {
  stroke: var(--text-muted, #94a3b8);
  stroke-width: 1.5;
  stroke-linecap: round;
  opacity: 0.5;
}

.hour-tick {
  stroke: var(--text-main, #0f172a);
  stroke-width: 3.5;
  stroke-linecap: round;
  opacity: 0.9;
}

.clock-number {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, sans-serif;
  font-size: 17px;
  font-weight: 800;
  fill: var(--text-main, #0f172a);
}

.hand {
  stroke-linecap: round;
}

.hour-hand {
  stroke: var(--text-main, #0f172a);
  stroke-width: 6.5;
}

.hour-tip {
  fill: var(--text-main, #0f172a);
}

.minute-hand {
  stroke: var(--primary, #3b82f6);
  stroke-width: 4.5;
}

.minute-tip {
  fill: var(--primary, #3b82f6);
}

.second-hand {
  stroke: #ef4444;
  stroke-width: 2.2;
}

.second-tail {
  fill: #ef4444;
}

.center-pin-base {
  fill: var(--bg-surface, #ffffff);
  stroke: var(--border-color, #cbd5e1);
  stroke-width: 1.5;
}

.center-pin {
  fill: var(--text-main, #0f172a);
}

.center-jewel {
  fill: #ef4444;
}

.analog-info-footer {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 480px;
}

/* Digital Stage */
.digital-stage {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-width: 640px;
}

.time-header-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 20px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
}

.pulse-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: blink 2s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}

.tz-offset {
  color: var(--primary, #3b82f6);
  font-weight: 700;
}

/* Huge Digital Numbers with Tabular Anti-Shake */
.hero-digital-time {
  display: flex;
  align-items: baseline;
  gap: 8px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-variant-numeric: tabular-nums;
  font-feature-settings: "tnum";
  line-height: 1;
}

.digits-group {
  display: flex;
  align-items: baseline;
  font-size: clamp(34px, 5.2vw, 56px);
  font-weight: 800;
  color: var(--text-main, #0f172a);
  letter-spacing: -2px;
  text-shadow: 0 4px 20px rgba(99, 102, 241, 0.15);
}

.digit-colon {
  margin: 0 2px;
  color: var(--primary, #6366f1);
  opacity: 0.85;
}

.digit-seconds {
  color: #6366f1;
}

.digit-milliseconds {
  font-size: 0.48em;
  color: #a855f7;
  font-weight: 700;
  margin-left: 2px;
}

.digit-ampm {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-muted, #64748b);
}

/* Calendar and Lunar Badges */
.calendar-detail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-surface, #f8fafc);
  border: 1px solid var(--border-color, #e2e8f0);
  border-radius: 12px;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-main, #1e293b);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
}

.icon-accent {
  color: var(--primary, #3b82f6);
}

.icon-lunar {
  color: #f59e0b;
}

.weekday-tag {
  background: rgba(59, 130, 246, 0.12);
  color: var(--primary, #3b82f6);
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 700;
}

/* Greeting and Day Progress Section */
.day-progress-section {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 4px;
}

.progress-info-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12.5px;
  font-weight: 600;
}

.greeting-text {
  color: var(--text-muted, #64748b);
}

.progress-percent {
  color: var(--primary, #6366f1);
  font-family: ui-monospace, monospace;
}

.day-progress-track {
  width: 100%;
  height: 6px;
  background: var(--border-color, #e2e8f0);
  border-radius: 6px;
  overflow: hidden;
}

.day-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
  border-radius: 6px;
  transition: width 1s linear;
}

/* ============================================================
   Enhanced Large-Scale Fullscreen & Zen Immersion Mode Styles
   ============================================================ */
.local-clock-container.is-fullscreen,
.local-clock-container.zen-fullscreen {
  padding: 20px 32px;
}

.is-fullscreen .clock-split-container,
.zen-fullscreen .clock-split-container {
  max-width: 1280px;
  gap: 56px;
}

/* Analog Clock in Fullscreen: Expand SVG dial from 210px to min(420px, 52vh) */
.is-fullscreen .analog-clock-svg,
.zen-fullscreen .analog-clock-svg {
  width: min(420px, 52vh);
  height: min(420px, 52vh);
  filter: drop-shadow(0 20px 48px rgba(0, 0, 0, 0.22));
}

.is-fullscreen .clock-col-right,
.zen-fullscreen .clock-col-right {
  max-width: 520px;
  gap: 20px;
}

.is-fullscreen .time-header-pill,
.zen-fullscreen .time-header-pill {
  padding: 7px 20px;
  font-size: 14px;
}

.is-fullscreen .detail-pill,
.zen-fullscreen .detail-pill {
  padding: 12px 22px;
  font-size: 15px;
  border-radius: 14px;
}

.is-fullscreen .greeting-text,
.zen-fullscreen .greeting-text {
  font-size: 15px;
}

.is-fullscreen .progress-percent,
.zen-fullscreen .progress-percent {
  font-size: 14px;
}

.is-fullscreen .day-progress-track,
.zen-fullscreen .day-progress-track {
  height: 8px;
}

/* Digital Clock in Fullscreen: Giant crystal-clear typography */
.is-fullscreen .digits-group,
.zen-fullscreen .digits-group {
  font-size: clamp(52px, 8vw, 108px);
  letter-spacing: -3px;
  text-shadow: 0 10px 40px rgba(99, 102, 241, 0.3);
}

.is-fullscreen .digit-ampm,
.zen-fullscreen .digit-ampm {
  font-size: clamp(20px, 2.5vw, 36px);
}

/* Flip Clock in Fullscreen & Zen Mode */
.is-fullscreen .flip-clock-stage,
.zen-fullscreen .flip-clock-stage {
  gap: clamp(18px, 2.8vw, 36px);
}

.is-fullscreen .flip-clock-stage.has-seconds,
.zen-fullscreen .flip-clock-stage.has-seconds {
  gap: clamp(12px, 1.8vw, 24px);
}

.is-fullscreen .flip-card-unit,
.zen-fullscreen .flip-card-unit {
  width: clamp(150px, 19vw, 230px);
  height: clamp(170px, 22vw, 255px);
  border-radius: 18px;
  box-shadow: 0 20px 48px rgba(0, 0, 0, 0.5), 0 6px 16px rgba(0, 0, 0, 0.3);
}

.is-fullscreen .flip-clock-stage.has-seconds .flip-card-unit,
.zen-fullscreen .flip-clock-stage.has-seconds .flip-card-unit {
  width: clamp(118px, 14.5vw, 172px);
  height: clamp(138px, 16.5vw, 195px);
  border-radius: 15px;
}

.is-fullscreen .flip-upper,
.zen-fullscreen .flip-upper {
  border-top-left-radius: 18px;
  border-top-right-radius: 18px;
}

.is-fullscreen .flip-clock-stage.has-seconds .flip-upper,
.zen-fullscreen .flip-clock-stage.has-seconds .flip-upper {
  border-top-left-radius: 15px;
  border-top-right-radius: 15px;
}

.is-fullscreen .flip-lower,
.zen-fullscreen .flip-lower {
  border-bottom-left-radius: 18px;
  border-bottom-right-radius: 18px;
}

.is-fullscreen .flip-clock-stage.has-seconds .flip-lower,
.zen-fullscreen .flip-clock-stage.has-seconds .flip-lower {
  border-bottom-left-radius: 15px;
  border-bottom-right-radius: 15px;
}

.is-fullscreen .flip-upper .flip-num,
.zen-fullscreen .flip-upper .flip-num,
.is-fullscreen .flip-lower .flip-num,
.zen-fullscreen .flip-lower .flip-num {
  font-size: clamp(96px, 13vw, 160px);
}

.is-fullscreen .flip-clock-stage.has-seconds .flip-upper .flip-num,
.zen-fullscreen .flip-clock-stage.has-seconds .flip-upper .flip-num,
.is-fullscreen .flip-clock-stage.has-seconds .flip-lower .flip-num,
.zen-fullscreen .flip-clock-stage.has-seconds .flip-lower .flip-num {
  font-size: clamp(74px, 9.6vw, 116px);
}

.is-fullscreen .flip-ampm-tag,
.zen-fullscreen .flip-ampm-tag {
  font-size: 14px;
  top: 12px;
  left: 14px;
}

/* Nixie Fullscreen */
.is-fullscreen .nixie-tube,
.zen-fullscreen .nixie-tube {
  width: clamp(56px, 7.2vw, 92px);
  height: clamp(100px, 13vw, 168px);
  border-radius: 40px 40px 10px 10px;
}
.is-fullscreen .nixie-digit,
.zen-fullscreen .nixie-digit {
  font-size: clamp(54px, 7vw, 94px);
}

/* Rings Fullscreen */
.is-fullscreen .rings-svg,
.zen-fullscreen .rings-svg {
  width: min(380px, 48vh);
  height: min(380px, 48vh);
}
.is-fullscreen .ring-center-time,
.zen-fullscreen .ring-center-time {
  font-size: 44px;
}

/* 7-Segment Fullscreen */
.is-fullscreen .seg-digit-box,
.zen-fullscreen .seg-digit-box {
  width: clamp(46px, 5.8vw, 76px);
  height: clamp(92px, 11.5vw, 150px);
}
.is-fullscreen .seg-a, .zen-fullscreen .seg-a,
.is-fullscreen .seg-d, .zen-fullscreen .seg-d,
.is-fullscreen .seg-g, .zen-fullscreen .seg-g {
  height: 8px;
}
.is-fullscreen .seg-b, .zen-fullscreen .seg-b,
.is-fullscreen .seg-c, .zen-fullscreen .seg-c,
.is-fullscreen .seg-e, .zen-fullscreen .seg-e,
.is-fullscreen .seg-f, .zen-fullscreen .seg-f {
  width: 8px;
}

/* Matrix Words Fullscreen */
.is-fullscreen .words-grid-card,
.zen-fullscreen .words-grid-card {
  padding: 20px 24px;
  gap: 12px;
}
.is-fullscreen .word-cell,
.zen-fullscreen .word-cell {
  width: clamp(30px, 3.8vw, 48px);
  height: clamp(30px, 3.8vw, 48px);
  font-size: clamp(16px, 1.9vw, 22px);
}

/* Compass Fullscreen */
.is-fullscreen .compass-svg,
.zen-fullscreen .compass-svg {
  width: min(580px, 78vh);
  height: min(580px, 78vh);
}

/* Responsive Breakpoints */
@media (max-width: 768px) {
  .clock-split-container {
    flex-direction: column;
    gap: 20px;
  }
  .clock-col-left {
    width: 100%;
  }
  .clock-col-right {
    align-items: center;
    max-width: 100%;
    width: 100%;
  }
  .calendar-detail-card {
    align-items: center;
  }
  .digits-group {
    font-size: 38px;
  }
  .flip-card-unit {
    width: 82px;
    height: 96px;
  }
  .flip-clock-stage.has-seconds .flip-card-unit {
    width: 62px;
    height: 74px;
  }
  .flip-upper .flip-num,
  .flip-lower .flip-num {
    font-size: 52px;
  }
  .flip-clock-stage.has-seconds .flip-upper .flip-num,
  .flip-clock-stage.has-seconds .flip-lower .flip-num {
    font-size: 38px;
  }
  .nixie-tube {
    width: 36px;
    height: 64px;
  }
  .nixie-digit {
    font-size: 36px;
  }
  .seg-digit-box {
    width: 26px;
    height: 52px;
  }
  .compass-svg {
    width: min(300px, 75vw);
    height: min(300px, 75vw);
  }
}
</style>
