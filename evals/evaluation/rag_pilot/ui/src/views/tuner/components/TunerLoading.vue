<template>
  <div v-if="props.visible" class="loading-container">
    <div class="loading-wrap">
      <a-spin :size="size" />
      <p
        class="loading-title"
        :style="{ fontSize: size === 'default' ? '14px' : '18px' }"
      >
        {{ title }}
      </p>
      <p class="loading-text" v-if="showDes">
        {{ describe }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts" name="xxx">
const props = defineProps({
  visible: {
    type: Boolean,
    required: true,
    default: false,
  },
  size: {
    type: String,
    default: "large",
  },
  title: {
    type: String,
    default: "Loading...",
  },
  describe: {
    type: String,
    default:
      "Please wait patiently and do not refresh the page during this period",
  },
  showDes: {
    type: Boolean,
    default: true,
  },
});
</script>

<style lang="less" scoped>
.loading-container {
  width: 100%;
  flex: 1;
  .vertical-center;
  .loading-wrap {
    text-align: center;
    padding: 24px;
    .loading-title {
      font-size: 18px;
      line-height: 28px;
      font-weight: 600;
      color: var(--font-main-color);
      margin: 8px auto;
    }
    .loading-text {
      line-height: 20px;
      color: var(--font-text-color);
    }
  }
}
</style>
