<template>
  <div class="rating-container">
    <QueryMenu
      :menu="resultsData"
      :current-id="activeSection"
      @updateId="handleUpdateId"
    />
    <div class="tip-wrap">
      <div class="tip-text">
        <StarFilled
          :style="{ fontSize: '16px', color: 'var(--color-warning)' }"
        />
        <span>{{ $t("common.ratingTip") }}</span>
      </div>
      <div class="rated-wrap slider-wrap">
        <span>{{ $t("common.rated") }}:</span>
        <a-slider v-model:value="rated" :min="0" :max="maxRated" /><span
          >{{ rated }}/{{ maxRated }}</span
        >
      </div>
    </div>
    <div class="rating-content">
      <template v-if="resultsData?.length">
        <div
          v-for="(item, index) in resultsData"
          :key="index"
          :id="item?.query_id?.toString()"
          ref="sectionRefs"
          class="query-item"
        >
          <div class="index-wrap">{{ index + 1 }}</div>
          <div class="query-wrap">
            <div class="query-title">
              <div class="left-wrap">
                <div class="id-wrap">#{{ index + 1 }}</div>
                <div class="title-wrap">{{ item.query }}</div>
              </div>
              <div class="right-wrap">
                <a-rate v-model:value="item.metadata!.answer_relevancy" />
              </div>
            </div>
            <div class="response-wrap" v-html="marked(item.response!)"></div>
          </div></div
      ></template>
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
      <TunerLoading
        :visible="loading.visible"
        :size="loading.size"
        :show-des="loading.showDes"
        :describe="$t('common.loadingTip')"
      />
    </div>
    <div class="footer-container">
      <a-button type="primary" ghost @click="handleExit">
        <template #icon>
          <SvgIcon name="icon-exit" :size="16" />
        </template>
        {{ $t("common.exit") }}</a-button
      >
      <div>
        <a-button
          v-if="!loading.visible"
          type="primary"
          ghost
          @click="handleSkip"
          >{{ $t("common.skip") }}
          <SvgIcon name="icon-skip1" :size="16" inherit class="ml-8" />
        </a-button>
        <a-button
          v-if="isCompleted"
          type="primary"
          :disabled="!allRated || loading.visible"
          @click="handleNext"
          >{{ $t("common.next") }}
          <ArrowRightOutlined />
        </a-button>
        <a-button v-if="!loading.visible" type="primary" @click="handleRun">
          {{ $t("common.start") }}
          <PlayCircleOutlined />
        </a-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="Rating">
import { ref, computed, onMounted } from "vue";
import { QueryMenu, TunerLoading } from "./index";
import {
  requestResultsMetrics,
  getResultsByPipelineId,
  requestPipelineRun,
  requestStageReset,
} from "@/api/ragPilot";
import { ResultOut } from "../type";
import {
  StarFilled,
  ArrowRightOutlined,
  PlayCircleOutlined,
} from "@ant-design/icons-vue";
import SvgIcon from "@/components/SvgIcon.vue";
import { debounce } from "lodash-es";
import { marked } from "marked";
import CustomRenderer from "@/utils/customRenderer";
import router from "@/router";
import { pipelineAppStore } from "@/store/pipeline";
import { Modal } from "ant-design-vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const pipelineStore = pipelineAppStore();

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});

const intervalId = ref<any>(null);
const timers = reactive<any>({});
const loading = reactive<EmptyObjectType>({
  visible: false,
  size: "large",
  showDes: true,
});
const pipelineId = ref<number | null>();
const resultsData = ref<ResultOut[]>([]);
const headerHeight = 46;
const sectionRefs = ref<HTMLElement[]>([]);
let scrollContainer: HTMLElement | null = null;
const activeSection = ref<number>();
const stageList = ref<string[]>(["retrieval", "postprocessing", "generation"]);
const isCompleted = ref<boolean>(false);

const rated = computed(() => {
  return (
    resultsData.value?.filter((result) => result?.metadata?.answer_relevancy)
      .length || 0
  );
});
const allRated = computed(() => {
  return resultsData.value.every((result) => result.metadata?.answer_relevancy);
});
const showNoData = computed(() => {
  return !loading.visible && !resultsData.value?.length;
});
const maxRated = computed(() => {
  return resultsData.value?.length || 0;
});
const handleUpdateId = (value: number) => {
  if (value) handleScrollTo(value!);
};
const handleQueryResult = async () => {
  loading.visible = true;
  getQueryResult();

  intervalId.value = setInterval(getQueryResult, 5000);
};
const getQueryResult = async () => {
  if (!scrollContainer) return;
  const prevScrollTop = scrollContainer.scrollTop;
  const data: any = (await getResultsByPipelineId(pipelineId.value!)) || [];
  if (data?.results?.length) {
    let newItems: any = [];
    data.results.forEach((item: any) => {
      if (!("answer_relevancy" in item.metadata)) {
        item.metadata.answer_relevancy = 0;
      }
      const existingItem = resultsData.value.find(
        (result) => result.query_id === item.query_id
      );
      if (!existingItem) {
        newItems.push(item);
      }
    });
    resultsData.value = [...resultsData.value, ...newItems];
    loading.size = "default";
    loading.showDes = false;
    await nextTick();
    scrollContainer.scrollTop = prevScrollTop;
    handleScroll();
  }
  if (data?.finished) {
    clearInterval(intervalId.value);
    loading.visible = false;
    isCompleted.value = true;
  }
};

const formatFormParam = () => {
  return resultsData.value.map((item) => {
    const { query_id, metadata } = item;

    return {
      query_id,
      metadata,
    };
  });
};

const handleNext = async () => {
  await requestResultsMetrics(pipelineId.value!, formatFormParam());
  router.push({ name: "Retrieve" });
};
const handleExit = async () => {
  Modal.confirm({
    title: t("common.prompt"),
    content: t("common.exitTip"),
    okText: t("common.confirm"),
    async onOk() {
      try {
        const promises = stageList.value.map((stage) =>
          requestStageReset(stage)
        );
        await Promise.all(promises);
        pipelineStore.setPipeline("");
        router.push({ name: "Home" });
      } catch (err) {
        console.log(err);
      }
    },
  });
};
const handleSkip = () => {
  if (intervalId.value) clearInterval(intervalId.value);
  router.push({ name: "Retrieve" });
};
const handlePipelineRun = async () => {
  loading.visible = true;
  pipelineId.value = pipelineStore.basePipeline;
  try {
    await requestPipelineRun(pipelineId.value!);
    handleQueryResult();
  } catch (err) {
    console.error(err);
    loading.visible = false;
  }
};
const handleScrollTo = (id: number) => {
  const element = document.getElementById(id.toString());

  if (element) {
    const offsetPosition = element.offsetTop - headerHeight;

    scrollContainer?.scrollTo({
      top: offsetPosition,
      behavior: "smooth",
    });
  }
};
const handleScroll = debounce(() => {
  const scrollPosition = scrollContainer?.scrollTop! + headerHeight + 20;

  for (let i = resultsData.value.length - 1; i >= 0; i--) {
    const section = sectionRefs.value[i];

    if (section) {
      const sectionTop = section.offsetTop;

      if (scrollPosition >= sectionTop) {
        if (activeSection.value !== resultsData.value[i].query_id) {
          activeSection.value = resultsData.value[i].query_id;
        }
        break;
      }
    }
  }
}, 100);
const handleRun = () => {
  handlePipelineRun();
};

onMounted(async () => {
  scrollContainer = document.querySelector(".layout-main");
  if (scrollContainer) {
    scrollContainer.addEventListener("scroll", handleScroll);
    handleScroll();
  }
});
onUnmounted(() => {
  scrollContainer?.removeEventListener("scroll", handleScroll);
  clearInterval(timers);
});
</script>

<style scoped lang="less">
.rating-container {
  padding-bottom: 64px;
  display: flex;
  width: 100%;
  .tip-wrap {
    z-index: 21;
    padding: 6px 3%;
    display: flex;
    width: 100vw;
    position: fixed;
    top: 128px;
    left: 0;
    color: var(--color-white);
    background-color: var(--color-primary-tip);
    box-shadow: 0px 1px 2px 0px var(--bg-box-shadow);
    .flex-between;
    .tip-text {
      display: flex;
      gap: 4px;
      align-items: center;
    }
    .rated-wrap {
      width: 300px;
      display: flex;
      gap: 4px;
      align-items: center;
      :deep(.intel-slider-horizontal) {
        flex: 1;
        top: -2px;
        .intel-slider-rail {
          height: 8px;
          border-radius: 4px;
        }
        .intel-slider-track {
          height: 8px;
          border-radius: 4px;
          background-color: var(--bg-card-color);
        }
        .intel-slider-handle::after {
          top: 1px;
        }
      }
    }
  }
  .rating-content {
    width: 100%;
    padding: 45px 0 24px;
    position: relative;
    .flex-column;
    .query-item {
      padding: 20px;
      border-radius: 6px;
      border: 1px solid var(--border-main-color);
      background-color: var(--bg-card-color);
      box-shadow: 0px 2px 4px 0px var(--bg-box-shadow);
      margin-top: 12px;
      width: 100%;
      .icon-loading {
        color: var(--color-primary) !important;
        animation: spin 3s linear infinite;
      }
      .right-wrap {
        height: max-content;
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
  .footer-container {
    .icon-exit {
      color: var(--color-primary) !important;
      margin-right: 6px;
    }
  }
}
</style>
