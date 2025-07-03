<template>
  <a-layout class="layout-container">
    <a-layout-header class="layout-header">
      <Header />
    </a-layout-header>
    <a-layout-content class="layout-main">
      <div class="layout-view">
        <router-view />
      </div>
    </a-layout-content>
  </a-layout>
</template>
<script lang="ts" setup name="Main">
import Header from "./Header.vue";
</script>
<style lang="less"></style>
