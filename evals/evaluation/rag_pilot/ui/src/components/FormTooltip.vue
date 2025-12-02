<template>
  <a-tooltip placement="topLeft" arrow-point-at-center>
    <template #title>
      {{ title }}
    </template>
    <component
      :is="iconComponent"
      :style="{ fontSize: size, color: 'var(--font-text-color)' }"
      v-bind="$attrs"
    />
  </a-tooltip>
</template>

<script setup lang="ts" name="FormTooltip">
import { computed } from "vue";
import { InfoCircleOutlined } from "@ant-design/icons-vue";
import * as icons from "@ant-design/icons-vue";

const props = defineProps({
  icon: {
    type: String,
    required: true,
    default: "InfoCircleOutlined",
    validator: (value: string) => {
      return value in icons;
    },
  },
  title: {
    type: String,
  },
  size: {
    type: String,
    default: () => "16px",
  },
});

const iconComponent = computed(() => {
  if (!(props.icon in icons)) {
    return InfoCircleOutlined;
  }
  return icons[props.icon as keyof typeof icons] as any;
});
</script>

<style lang="less" scoped></style>
