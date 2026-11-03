import { createApp } from 'vue';
import { createPinia } from 'pinia';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';

import App from './App.vue';
import router from './router';
import SvgIcon from './components/common/SvgIcon.vue';

import './styles/theme.css';
import './styles/main.css';

/**
 * 医疗物资全链路管理系统前端 Vue 3 启动入口
 * @returns void
 * @route internal://src/main.ts
 * @throws 当 DOM 节点 #app 不存在时抛出异常
 */
function bootstrap() {
  const app = createApp(App);
  const pinia = createPinia();

  app.use(pinia);
  app.use(router);
  app.use(ElementPlus);
  app.component('SvgIcon', SvgIcon);

  app.mount('#app');
}

bootstrap();
