<template>
  <div class="prompt-container">
    <div class="title-wrap">{{ $t("prompt.activated") }}</div>
    <div class="content-wrap">
      <TunerLoading :visible="loading" />
      <a-row type="flex" wrap :gutter="[20, 20]" v-if="promptList.length">
        <a-col :span="8" v-for="(prompt, index) in promptList" :key="index">
          <div
            :class="{
              'card-wrap': true,
              'select-wrap': index === currentPrompt,
            }"
            @click="handleSelect(prompt, index)"
          >
            <span class="active-icon" v-if="index === currentPrompt"
              ><CheckOutlined :style="{ fontSize: '12px' }"
            /></span>
            <div class="header-wrap">
              <span class="name-wrap">
                <template v-if="index">
                  {{ `${$t("prompt.title")} ${index}` }}</template
                >
                <template v-else>
                  {{ $t("prompt.original") }}
                </template>
              </span>
            </div>
            <div class="data-wrap">
              <div class="tex-wrap" v-html="marked(prompt)"></div>
            </div>
            <div class="footer-wrap" v-if="false">
              <div class="item-icon" @click.prevent="handleUpdate(prompt)">
                <EditFilled />
                {{ $t("common.edit") }}
              </div>
            </div>
          </div>
        </a-col>
      </a-row>
      <a-empty class="no-data" v-if="showNoData">
        <template #description>
          <p class="empty-title">
            {{ $t("common.noData") }}
          </p>
          <p class="empty-text">
            {{ $t("common.runTip") }}
          </p>
        </template>
      </a-empty>
    </div>
    <div class="footer-container">
      <div>
        <a-button type="primary" ghost @click="handleBack" v-if="!inProgress">
          <ArrowLeftOutlined />
          {{ $t("common.back") }}
        </a-button>
        <a-button type="primary" ghost @click="handleExit">
          <LogoutOutlined />
          {{ $t("common.exit") }}
        </a-button>
      </div>
      <div>
        <a-button type="primary" ghost @click="handleSkip"
          >{{ $t("common.skip") }}
          <SvgIcon name="icon-skip1" :size="16" inherit class="ml-8" />
        </a-button>
        <template v-if="!inProgress">
          <a-button
            class="next-btn"
            type="primary"
            @click="handleConfiguretuner"
            >{{ $t("tuner.configure") }} <SettingOutlined
          /></a-button>

          <a-button type="primary" @click="handleRunTuner">
            {{ $t("common.run") }}
            <PlayCircleOutlined /> </a-button
        ></template>
        <a-button type="primary" @click="handleNext" v-if="showNext">
          {{ $t("common.next") }}
          <ArrowRightOutlined />
        </a-button>
      </div>
    </div>
    <UpdateDrawer
      v-if="updateDrawer.visible"
      :drawer-data="updateDrawer.data"
      @close="updateDrawer.visible = false"
    />
    <!-- TunerConfigure -->
    <TunerConfigure
      v-if="tunerConfigure.visible"
      :stage="tunerConfigure.type"
      @confirm="handleUpdateConfiguration"
      @close="tunerConfigure.visible = false"
    />
  </div>
</template>

<script lang="ts" setup name="Prompt">
import { TunerLoading } from "./index";
import "vue-json-pretty/lib/styles.css";
import {
  EditFilled,
  CheckOutlined,
  ArrowLeftOutlined,
  LogoutOutlined,
  PlayCircleOutlined,
  SettingOutlined,
  ArrowRightOutlined,
} from "@ant-design/icons-vue";
import { themeAppStore } from "@/store/theme";
import UpdateDrawer from "./UpdateDrawer.vue";
import router from "@/router";
import { marked } from "marked";
import CustomRenderer from "@/utils/customRenderer";
import { TunerConfigure } from "./index";

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});

const props = defineProps({
  prompts: {
    type: Array,
    required: true,
    default: () => [],
  },
  loading: {
    type: Boolean,
    required: true,
    default: () => false,
  },
  inProgress: {
    type: Boolean,
    required: true,
    default: () => false,
  },
  isInit: {
    type: Boolean,
    required: true,
    default: () => false,
  },
});

const themeStore = themeAppStore();
const emit = defineEmits(["run", "exit", "next"]);

const tunerConfigure = reactive<DialogType>({
  type: "generation",
  data: {},
  visible: true,
});
const showNext = computed(() => {
  return !!props.prompts?.length;
});
const showNoData = computed(() => {
  return !props.loading && !props.prompts?.length;
});
const currentTheme = computed(() => {
  return themeStore.theme || "light";
});
const currentPrompt = ref<number | null>(null);
const updateDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});
const promptList = ref<EmptyArrayType>(props.prompts);
const handleSelect = (data: EmptyObjectType, index: number) => {
  return;
  currentPrompt.value = index;
};
//edit
const handleUpdate = async (row: EmptyObjectType) => {
  updateDrawer.data = row;
  updateDrawer.visible = true;
};
const handleConfiguretuner = () => {
  tunerConfigure.visible = true;
  tunerConfigure.data = [];
};
const handleUpdateConfiguration = () => {
  tunerConfigure.visible = false;
  handleRunTuner();
};
const handleSkip = () => {
  router.push({ name: "Results" });
};
const handleBack = async () => {
  router.push({ name: "Postprocess" });
};
const handleRunTuner = async () => {
  emit("run");
};
const handleExit = () => {
  emit("exit");
};
const handleNext = async () => {
  emit("next");
};
watch(
  () => props.prompts,
  async (prompts) => {
    promptList.value = prompts;
  },
  { immediate: true, deep: true }
);
watch(
  () => props.isInit,
  (init) => {
    console.log(init);
    if (!init) tunerConfigure.visible = false;
  },
  { immediate: true, deep: true }
);
</script>

<style scoped lang="less">
.prompt-container {
  padding: 20px 0;
  width: 100%;
  height: 100%;
  .title-wrap {
    font-size: 24px;
    font-weight: 600;
    color: var(--font-main-color);
  }
  .content-wrap {
    margin-top: 32px;
    width: 100%;
    height: 100%;
    position: relative;
    .flex-column;
    .card-wrap {
      background-color: var(--bg-content-color);
      padding: 20px;
      position: relative;
      height: 360px;
      border-radius: 8px;
      .flex-column;
      gap: 12px;
      border: 2px solid var(--bg-content-color);
      &:hover {
        .card-shadow;
      }
      .header-wrap {
        .name-wrap {
          background-color: var(--color-deep-primaryBg);
          color: var(--color-primary-second);
          padding: 2px 12px;
          border-radius: 12px;
        }
      }

      .data-wrap {
        flex: 1;
        overflow-y: auto;
        padding: 8px;
        border-radius: 6px;
        background-color: var(--bg-second-color);
      }
      .footer-wrap {
        height: 24px;
        .flex-end;
        .item-icon {
          .vertical-center;
          gap: 8px;
          cursor: pointer;
          color: var(--color-primary);
          &:hover {
            color: var(--color-primary-hover);
          }
        }
      }
      &.select-wrap {
        border: 2px solid var(--color-success);
      }
      .active-icon {
        position: absolute;
        right: -1px;
        top: -1px;
        border-radius: 0 6px 0 6px;
        width: 18px;
        height: 18px;
        background-color: var(--color-success);
        color: var(--color-white);
        .vertical-center;
      }
    }
  }
  .no-data {
    margin: auto;
    .empty-title {
      font-size: 18px;
      line-height: 28px;
      font-weight: 600;
      color: var(--font-main-color);
      margin: 8px auto;
    }
    .empty-text {
      line-height: 20px;
      color: var(--font-text-color);
    }
  }
}
</style>
