<template>
  <div id="app">
    <router-view></router-view> <!-- 路由视图，会根据当前路由显示 Login 或 QueryForm -->
  </div>
</template>

<script>
export default {
  name: 'App'
};
</script>

<style>
/* 样式根据需要调整 */
</style>
