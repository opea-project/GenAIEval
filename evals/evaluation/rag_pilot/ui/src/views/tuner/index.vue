<template>
  <div class="tuner-container">
    <div class="process-container">
      <div class="process-menu">
        <a-steps :current="currentStep">
          <a-step
            v-for="menu in stepList"
            :key="menu.index"
            :class="['menu-wrap']"
          >
            <template #icon>
              <span class="icon-wrap">
                <SvgIcon :name="getStatusIcon(menu)" :size="18"
              /></span>
            </template>
            <template #title>
              <span @click="handleClickStep(menu)">{{ $t(menu.title) }}</span>
            </template>
          </a-step>
        </a-steps>
      </div>
    </div>
    <div class="body-wrap intel-markdown">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts" name="TunerProcess">
import router from "@/router";
import { ref } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const route = useRoute();

const currentStep = ref<number>(0);
const stepList = ref<EmptyArrayType>([
  {
    index: 0,
    title: "tuner.rating",
    icon: "icon-rating",
    name: "Rating",
  },
  {
    index: 1,
    title: "tuner.retriever",
    icon: "icon-retriever",
    name: "Retrieve",
  },
  {
    index: 2,
    title: "tuner.processor",
    icon: "icon-post-processor",
    name: "Postprocess",
  },
  {
    index: 3,
    title: "tuner.generator",
    icon: "icon-generator",
    name: "Generation",
  },
  {
    index: 4,
    title: "tuner.results",
    icon: "icon-results",
    name: "Results",
  },
]);

const getStatusIcon = (menu: EmptyObjectType) => {
  const { index, icon } = menu;

  if (index < currentStep.value) {
    return "icon-copy-success";
  } else if (index === currentStep.value) {
    return "icon-process-node";
  } else {
    return icon;
  }
};
const getCurrentStep = (name: any) => {
  currentStep.value = stepList.value.find((item) => item.name === name)?.index;
};
const handleClickStep = (step: any) => {
  const { index, name } = step;

  if (index < currentStep.value) {
    router.push({ name });
  }
};
watch(
  () => route.name,
  (name) => {
    getCurrentStep(name);
  },
  {
    deep: true,
    immediate: true,
  }
);
</script>

<style lang="less" scoped>
.tuner-container {
  height: 100%;
  padding-top: 64px;
  display: flex;
  flex-direction: column;
  .process-container {
    z-index: 21;
    position: fixed;
    top: 64px;
    left: 0;
    display: flex;
    width: 100vw;
    background-color: var(--bg-content-color);
  }
  .process-menu {
    width: 100%;
    padding: 16px 3%;
    background-color: var(--color-second-primaryBg);
    box-shadow: 0px 1px 2px 0px var(--bg-box-shadow);
    .menu-wrap {
      display: flex;
      .title-wrap {
        word-break: normal;
      }
    }
    .icon-wrap {
      .vertical-center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: var(--bg-second-color);
      border: 1px solid var(--color-switch-theme);
    }
    :deep(.intel-steps) {
      .intel-steps-item-title::after {
        height: 3px;
      }
      .intel-steps-item-finish
        .intel-steps-item-icon
        > .intel-steps-icon
        .icon-wrap {
        background-color: var(--color-primary-hover);
        .icon-copy-success {
          color: var(--color-white) !important;
        }
      }
      .intel-steps-item-process
        .intel-steps-item-icon
        > .intel-steps-icon
        .icon-wrap {
        background-color: var(--color-deep-primaryBg);
        .icon-process-node {
          color: var(--color-primary) !important;
        }
      }
    }
  }
  .body-wrap {
    flex: 1;
    display: flex;
    position: relative;
  }
}
</style>
