<template>
  <main id="hero-main-stage" class="hero-stage-center" role="region" aria-label="展厅核心舞台">
    <!-- 状态微徽标 -->
    <div class="hero-pill-badge">
      <span class="badge-live-pulse"></span>
      <span id="center-badge-text">医疗物资全链路 SPD · 双模态自适应数字化展厅 v2.0</span>
    </div>

    <!-- 主标题 -->
    <h1 class="hero-h1">
      智慧医疗 物资全链<br />
      <span class="gradient-span">全生命周期物权穿透与智能协同</span>
    </h1>

    <!-- 副标题描述 -->
    <p class="hero-summary-p">
      支持 360° 环形拓扑与 3D 弧面时间流双模态切换，直连本地 Wallpaper Engine 431960 全量 41 款创意工坊，支持 4K 原生动态视频无损播放与一键纯享。
    </p>

    <!-- CTA 核心按钮组 -->
    <div class="cta-btn-group">
      <!-- 流体笔刷主入口按钮 (微动效 ①) -->
      <button
        id="btn-enter-workbench"
        type="button"
        class="spd-fluid-btn"
        @click="handleEnterWorkbench"
      >
        <div class="spd-fluid-line"></div>
        <div class="spd-fluid-line"></div>
        <span class="spd-fluid-text">
          <SvgIcon name="arrow-right" size="14" color="currentColor" />
          <span>进入三级角色工作台</span>
          <span class="spd-fluid-badge">ENTRY</span>
        </span>
        <div class="spd-fluid-drow1"></div>
        <div class="spd-fluid-drow2"></div>
      </button>

      <!-- 快捷进入纯享壁纸态按钮 -->
      <button
        id="btn-quick-zen-cta"
        type="button"
        class="btn-cta-secondary"
        title="进入 100% 绝对纯净壁纸纯享模式 (快捷键 ESC)"
        @click="showcaseStore.setZenMode(true)"
      >
        <SvgIcon name="zen" size="16" />
        <span>进入纯享壁纸态 (ESC)</span>
      </button>

      <!-- 自由换图/选视频按钮 -->
      <button
        id="btn-trigger-picker-cta"
        type="button"
        class="btn-cta-secondary"
        title="打开壁纸工坊自由选图与换视频"
        @click="showcaseStore.toggleWallpaperDrawer(true)"
      >
        <SvgIcon name="wallpaper" size="16" />
        <span>自由选图/换视频</span>
      </button>
    </div>

    <!-- 底部三大法定合规指标卡 -->
    <div class="legal-metrics-grid">
      <div class="metric-col">
        <div class="metric-title">
          <SvgIcon name="shield" size="16" color="#0284c7" />
          <span>100% 审计穿透</span>
        </div>
        <div class="metric-desc">
          6W 物权交接流转全流程日志闭环，满足医保与卫健委飞行检查要求。
        </div>
      </div>

      <div class="metric-col">
        <div class="metric-title">
          <SvgIcon name="calendar" size="16" color="#10b981" />
          <span>一物一码单品</span>
        </div>
        <div class="metric-desc">
          高值专仓拆包赋唯一 UDI 序列号，扫码核销绑定患者住院号并合规脱敏。
        </div>
      </div>

      <div class="metric-col">
        <div class="metric-title">
          <SvgIcon name="scale" size="16" color="#f59e0b" />
          <span>移库不计费</span>
        </div>
        <div class="metric-desc">
          院内科室调拨不计入成本，临床实际消耗即结算，理顺医院财务内控。
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useShowcaseStore } from '@/stores/showcaseStore';
import { useUserStore } from '@/stores/userStore';
import SvgIcon from '@/components/common/SvgIcon.vue';

/**
 * @file HeroSection.vue
 * @description 中央毛玻璃 Hero 核心舱组件
 * 封装了高质感磨砂中心卡片、流体流动笔刷按钮、纯享触发入口及三大法定合规指标栏。
 */

const router = useRouter();
const showcaseStore = useShowcaseStore();
const userStore = useUserStore();

/**
 * 响应点击“进入三级角色工作台”
 * 若未登录则唤起安全模态登录中枢；若已登录则依据 RBAC 角色定向跳转对应模块
 * @param {void} 无入参
 * @returns {void}
 * @route internal://src/components/showcase/HeroSection.vue/handleEnterWorkbench
 * @throws 无异常抛出
 */
function handleEnterWorkbench(): void {
  if (!userStore.isLoggedIn) {
    showcaseStore.openLoginModal(true);
    return;
  }
  const role = userStore.currentUser.roleCode;
  if (role === 'secondary_user') {
    router.push('/secondary');
  } else if (role === 'finance_auditor') {
    router.push('/finance');
  } else if (role === 'supplier_user') {
    router.push('/procurement');
  } else {
    router.push('/dict');
  }
}
</script>

<style scoped>
.hero-stage-center {
  position: relative;
  z-index: 50;
  max-width: 820px;
  width: 90%;
  padding: 38px 32px 30px;
  background: var(--bg-card);
  -webkit-backdrop-filter: blur(28px) saturate(2);
  backdrop-filter: blur(28px) saturate(2);
  border: 1px solid var(--border-card);
  border-radius: 28px;
  box-shadow: 0 24px 64px -12px rgba(0, 0, 0, 0.35), 0 0 0 1px rgba(255, 255, 255, 0.15) inset;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: auto;
  transition: opacity 300ms ease-out, transform 300ms ease-out;
}

.hero-pill-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 5px 14px;
  border-radius: var(--radius-pill);
  background: rgba(2, 132, 199, 0.1);
  border: 1px solid rgba(2, 132, 199, 0.25);
  color: var(--accent-primary);
  font-size: 12px;
  font-weight: 600;
  margin-bottom: 18px;
}

.badge-live-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.95);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
  }
  100% {
    transform: scale(0.95);
    opacity: 0.8;
  }
}

.hero-h1 {
  font-size: 38px;
  font-weight: 800;
  line-height: 1.16;
  letter-spacing: -1px;
  color: var(--text-primary);
  margin-bottom: 12px;
}

.gradient-span {
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.hero-summary-p {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary);
  max-width: 620px;
  margin: 0 auto 24px;
}

.cta-btn-group {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 28px;
  flex-wrap: wrap;
}

.btn-cta-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  border-radius: var(--radius-pill);
  background: var(--bg-card);
  color: var(--text-primary);
  font-size: 14px;
  font-weight: 600;
  border: 1px solid var(--border-card);
  cursor: pointer;
  transition: transform 120ms ease-out, background 150ms ease-out, border-color 150ms ease-out;
  text-decoration: none;
}

.btn-cta-secondary:hover {
  background: var(--bg-card-hover);
  border-color: var(--accent-primary);
}

.btn-cta-secondary:active {
  transform: scale(0.96);
}

.legal-metrics-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-top: 1px solid var(--border-divider);
  padding-top: 20px;
  gap: 16px;
}

.metric-col {
  padding: 0 10px;
  text-align: center;
}

.metric-col:not(:last-child) {
  border-right: 1px solid var(--border-divider);
}

.metric-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.metric-desc {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.45;
}
</style>
