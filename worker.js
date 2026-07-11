// 极简 Worker：只负责把静态文件（docs/wiki/）serve 出去。
// 以后想加动态逻辑（统计、鉴权、改写响应等），在这里写即可。
export default {
  async fetch(request, env) {
    return env.ASSETS.fetch(request);
  }
};
