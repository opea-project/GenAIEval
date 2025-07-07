<template>
  <div class="postprocess-container">
    <QueryMenu
      :menu="resultsData"
      @updateId="handleUpdateId"
      @switch="handleSwitchQuery"
    />
    <div class="main-wrap">
      <div class="tuner-wrap">
        <a-steps label-placement="vertical">
          <a-step
            v-for="menu in tunerList"
            :key="menu.index"
            :class="['menu-wrap']"
          >
            <template #title>
              <span>{{ transformTunerName(menu.name) }}</span>
            </template>
            <template #icon>
              <span
                :class="[
                  'icon-wrap',
                  menu.status === 'completed' ? 'icon-done' : '',
                  menu.status === 'inactive' ? 'icon-warring' : '',
                ]"
              >
                <SvgIcon :name="getStatusIcon(menu)" :size="18"
              /></span>
            </template>
          </a-step>
        </a-steps>
      </div>
      <div v-if="!tunerDone" class="warring-tip">
        <ExclamationCircleFilled />
        {{ $t("common.waitTip") }}
      </div>
      <div class="chart-container">
        <div class="title-wrap">{{ $t("postprocess.pipelineRecall") }}</div>
        <v-chart class="chart-line" :option="lineChartOption" autoresize />
      </div>
      <div class="suggestion-wrap"></div>
      <div class="select-wrap" v-if="pipelineList?.length">
        {{ $t("postprocess.top_n") }} :
        <div
          v-for="item in pipelineList"
          :key="item.pipeline_id"
          :class="{
            'option-wrap': true,
            'is-active': item.pipeline_id === activePipelineId,
          }"
          @click="handleTopnChange(item.pipeline_id)"
        >
          <SettingFilled :style="{ color: 'var(--color-warning)' }" />
          {{ item.top_n }}
        </div>
      </div>
      <div class="ground-truth" id="Query" v-if="currentQuery.query_id">
        <a-affix :offset-top="64" :target="getScrollContainer">
          <div class="query-item">
            <div class="index-wrap">{{ currentQueryIndex }}</div>
            <div class="query-wrap">
              <div class="query-title">
                <div class="left-wrap">
                  <div class="id-wrap">#{{ currentQuery.query_id }}</div>
                  <div class="title-wrap">{{ currentQuery.query }}</div>
                </div>
                <div class="flex-end search-wrap">
                  <a-input
                    v-model:value="keywords"
                    :placeholder="t('postprocess.search')"
                    @blur="handleSearch"
                    @pressEnter="handleSearch"
                  >
                    <template #prefix>
                      <SearchOutlined />
                    </template>
                  </a-input>
                </div>
              </div>
            </div>
          </div>
        </a-affix>
        <div class="contexts-container">
          <div class="top-wrap">
            <div class="left-wrap">
              <span class="title-wrap">{{ $t("retriever.gt_context") }} </span>
              <a-tag color="success">
                {{ $t("retriever.recall") }} :
                {{ recallRate }}
              </a-tag>
            </div>
            <a-tag color="processing">
              {{ $t("common.total") }}: {{ contextsTotal }}</a-tag
            >
          </div>
          <div
            class="context-wrap"
            v-for="(context, index) in currentQuery.gt_contexts"
            :key="context.context_idx"
          >
            <div class="id-wrap">{{ index + 1 }}</div>
            <div class="content-wrap">
              <div class="top-wrap">
                <span class="file-name">
                  <a-tag :bordered="false">
                    {{ context.file_name }}
                  </a-tag></span
                >
              </div>
              <div class="text-wrapper" ref="groundTruthRefs">
                <div
                  :class="{
                    'text-content': true,
                    ellipsis: showContextText[index],
                    expanded: expandedMap[index],
                  }"
                  v-html="marked(context.text!)"
                ></div>
                <p
                  v-if="showContextText[index]"
                  @click="toggleExpand(index)"
                  class="expand-link"
                >
                  {{
                    expandedMap[index]
                      ? $t("common.collapse")
                      : $t("common.expand")
                  }}
                  <UpOutlined v-if="expandedMap[index]" />
                  <DownOutlined v-else />
                </p>
              </div>
            </div>
            <div class="hit-wrap">
              <div
                :class="{
                  'hit-item': true,
                  'active-hit': context?.retrievalHit,
                }"
              >
                <div class="hit-icon">Hit</div>
                {{ $t("postprocess.retrieved") }}
              </div>
              <div class="line-wrap"></div>
              <div
                :class="{
                  'hit-item': true,
                  'active-hit': context?.postprocessHit,
                }"
              >
                <div class="hit-icon">Hit</div>
                {{ $t("postprocess.postprocessed") }}
              </div>
            </div>
          </div>
        </div>
        <div id="Postprocess" class="contexts-container postprocess-wrap mt-16">
          <div class="top-wrap">
            <div class="left-wrap">
              <span class="title-wrap">{{ $t("postprocess.chunk") }}</span>
            </div>
            <a-tag color="success"
              >{{ $t("common.total") }}: {{ postprocessTotal }}</a-tag
            >
          </div>
          <div
            class="context-wrap"
            v-for="(postprocess, k) in postprocessSearchData"
            :key="postprocess.context_idx"
          >
            <div class="id-wrap">{{ k + 1 }}</div>
            <div class="content-wrap">
              <div class="top-wrap">
                <span class="file-name">
                  <a-tag :bordered="false">
                    {{ postprocess.file_name }}
                  </a-tag></span
                >
              </div>
              <div class="text-wrapper" ref="postprocessRefs">
                <div
                  :class="{
                    'text-content': true,
                    ellipsis: showPostprocessText[k],
                    expanded: expandedPostprocessMap[k],
                  }"
                  v-html="marked(postprocess.highlightedText!)"
                ></div>
                <p
                  v-if="showPostprocessText[k]"
                  @click="togglePostprocessExpand(k)"
                  class="expand-link"
                >
                  {{
                    expandedPostprocessMap[k]
                      ? $t("common.collapse")
                      : $t("common.expand")
                  }}
                  <UpOutlined v-if="expandedPostprocessMap[k]" />
                  <DownOutlined v-else />
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="footer-container">
      <a-button type="primary" ghost @click="handleBack">
        <ArrowLeftOutlined />
        {{ $t("common.back") }}
      </a-button>

      <div>
        <span class="text-wrap">
          <InfoCircleFilled
            :style="{ fontSize: '16px', color: 'var(--color-warning)' }"
          />
          {{ $t("postprocess.tip") }}
        </span>
        <a-button type="primary" :disabled="!tunerDone" @click="handleNext">
          {{ $t("common.next") }}
          <ArrowRightOutlined />
        </a-button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup name="postprocess">
import { ref, reactive, computed, onMounted, watch } from "vue";
import { QueryMenu } from "./index";
import {
  requesStageRun,
  getStagePipelines,
  getMetricsByStage,
  getResultsByStage,
  requesTopnUpdate,
  getTunerStatus,
} from "@/api/ragPilot";
import {
  UpOutlined,
  DownOutlined,
  InfoCircleFilled,
  ArrowRightOutlined,
  SettingFilled,
  ArrowLeftOutlined,
  ExclamationCircleFilled,
  SearchOutlined,
} from "@ant-design/icons-vue";
import { formatPercentage, transformTunerName } from "@/utils/common";
import { ResultOut } from "../type";
import { LineChart } from "echarts/charts";
import {
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  GridComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { Modal } from "ant-design-vue";
import CustomRenderer from "@/utils/customRenderer";
import { marked } from "marked";
import router from "@/router";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});
echarts.use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const isInit = ref<boolean>(true);
let scrollContainer: any = null;
const resultsData = ref<ResultOut[]>([]);
const pipelineList = ref<EmptyArrayType>([]);
const activePipelineId = ref<number>();
const currentQuery = reactive<ResultOut>({});
const currentQueryId = ref<number>();
const timers = reactive<any>({});
let tunerList = ref<EmptyArrayType>([]);
let allResult = reactive<EmptyObjectType>({});
const keywords = ref<string>("");
const showContextText = ref<boolean[]>([]);
const expandedMap = ref<boolean[]>([]);
const showPostprocessText = ref<boolean[]>([]);
const expandedPostprocessMap = ref<boolean[]>([]);
const lineChartOption = computed(() => ({
  grid: { top: 50, right: 20, bottom: 50, left: 50 },
  tooltip: {
    formatter: (params: any) => {
      return params.value + "%";
    },
  },
  legend: { data: [t("retriever.recall")], right: 15 },
  xAxis: {
    name: "Top n",
    nameLocation: "center",
    nameGap: 28,
    nameTextStyle: {
      fontWeight: "bold",
      fontSize: "14",
    },
    boundaryGap: false,
    data: pipelineList.value.map((item) => item.top_n),
  },
  yAxis: [
    {
      type: "value",
      min: 0,
      max: 100,
      interval: 20,
      name: t("retriever.recall"),
      nameGap: 20,
      nameTextStyle: {
        fontWeight: "bold",
        fontSize: "14",
      },
      splitLine: {
        show: true,
        lineStyle: { type: "dashed", color: "#f5f5f5" },
      },
      axisLabel: {
        formatter: "{value}%",
      },
    },
  ],
  series: [
    {
      name: t("retriever.recall"),
      type: "line",
      symbolSize: 6,
      symbol: "circle",
      smooth: true,
      data: pipelineList.value.map((item) =>
        (item.postprocessing_recall_rate * 100).toFixed(2)
      ),
      lineStyle: { color: "#9E87FF" },
      itemStyle: { color: "#9E87FF", borderColor: "#9E87FF" },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "#9E87FFb3" },
          { offset: 1, color: "#9E87FF03" },
        ]),
      },
    },
  ],
}));
const tunerDone = computed(() => {
  const statusList = ["completed", "inactive"];
  return tunerList.value?.every((item) => statusList.includes(item.status));
});

const getScrollContainer = () =>
  document.querySelector(".layout-main") as HTMLElement;
const postprocessSearchData = computed(() => {
  const { postprocessing_contexts = [] } = currentQuery;
  const kw = keywords.value.trim();
  if (!kw) {
    return postprocessing_contexts.map((item) => ({
      ...item,
      highlightedText: item.text,
    }));
  }
  const escapeRegExp = (text: string) =>
    text.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
  const safeKw = escapeRegExp(kw);
  const regex = new RegExp(`(${safeKw})`, "gi");
  return postprocessing_contexts.map((item) => ({
    ...item,
    highlightedText: item.text.replace(
      regex,
      "<mark class='highlighted'>$1</mark>"
    ),
  }));
});
const handlePostprocessRun = async () => {
  const data: any = await requesStageRun("postprocessing");
  const tunerData = data
    ?.filter((item: any) => item.status !== "inactive")
    .map((item: any) => item.name);

  tunerList.value = tunerData.map((item: any) => {
    return {
      name: item,
      status: "process",
    };
  });
  handleTunerStatus(tunerData);
};
const handleTunerStatus = async (tnnerLiist: any) => {
  tnnerLiist.forEach((tunerName: any) => {
    queryTunerStatus(tunerName);
    timers[tunerName] = setInterval(() => queryTunerStatus(tunerName), 5000);
  });
};
const queryTunerStatus = async (tunerName: string) => {
  const status: any = await getTunerStatus(tunerName);
  const statusList = ["completed", "inactive"];
  if (statusList.includes(status)) {
    tunerList.value.forEach((item) => {
      if (item.name === tunerName) item.status = status;
    });
    clearInterval(timers[tunerName]);
    delete timers[tunerName];
    queryStagePipelines();
    queryStageResults();
    if (tunerDone.value) {
      clearTimers();
    }
  }
};
const getStatusIcon = (menu: EmptyObjectType) => {
  const { status } = menu;

  if (status === "completed") {
    return "icon-copy-success";
  } else if (status === "inactive") {
    return "icon-skip";
  } else {
    return "icon-loading1";
  }
};
const getCurrentQuery = async () => {
  let queryData: any =
    resultsData.value.find((item) => item?.query_id === currentQueryId.value) ||
    {};

  queryData?.gt_contexts?.forEach((item: any) => {
    item.retrievalHit = !!item.metadata?.retrieval?.length;
    item.postprocessHit = !!item.metadata?.postprocessing?.length;
  });
  Object.assign(currentQuery, queryData);
  handleMapReset();
  nextTick(() => {
    checkTextOverflow();
    handleScrollQuery();
  });
};
const currentQueryIndex = computed(() => {
  return (
    resultsData.value?.findIndex(
      (item) => item?.query_id === currentQueryId.value
    ) + 1
  );
});
const handleTopnChange = (id: number) => {
  activePipelineId.value = id;
  handleResultsBuyCurrentPipeline();
};
const toggleExpand = (index: number) => {
  expandedMap.value[index] = !expandedMap.value[index];
};
const togglePostprocessExpand = (index: number) => {
  expandedPostprocessMap.value[index] = !expandedPostprocessMap.value[index];
};
const groundTruthRefs = ref<Array<HTMLElement | null>>([]);
const postprocessRefs = ref<Array<HTMLElement | null>>([]);
const selectedPipeline = computed(() => {
  return pipelineList.value?.find(
    (item) => item?.pipeline_id === activePipelineId.value
  );
});
const contextsTotal = computed(() => {
  return currentQuery?.gt_contexts?.length || 0;
});
const postprocessTotal = computed(() => {
  return currentQuery.postprocessing_contexts?.length || 0;
});
const recallRate = computed(() => {
  const { gt_contexts = [] } = currentQuery;
  const count = gt_contexts.filter(
    (item) => item.metadata?.postprocessing?.length
  ).length;
  return `${formatPercentage(count / contextsTotal.value)}(${count}/${
    contextsTotal.value
  })`;
});

const handleSearch = async () => {
  const element = document.getElementById("Postprocess");

  if (element) {
    const offsetPosition = element.offsetTop - 140;

    scrollContainer?.scrollTo({
      top: offsetPosition,
      behavior: "smooth",
    });
  }
  const { postprocessing_contexts = [] } = currentQuery;
  expandedPostprocessMap.value = postprocessing_contexts.map(() => true);
};
const handleBack = async () => {
  router.push({ name: "Retrieve" });
};
const handleNext = async () => {
  Modal.confirm({
    title: t("common.prompt"),
    content: `${t("postprocess.tip1")} ${selectedPipeline.value.top_n}${t(
      "postprocess.tip2"
    )}`,
    okText: t("common.confirm"),
    async onOk() {
      await requesTopnUpdate(selectedPipeline.value.top_n);
      router.push({ name: "Generation" });
    },
  });
};
const handleScrollQuery = async () => {
  const element = document.getElementById("Query");

  if (element) {
    const offsetPosition = isInit.value ? 0 : element.offsetTop;
    scrollContainer?.scrollTo({
      top: offsetPosition,
      behavior: "smooth",
    });
  }
};
const handleMapReset = () => {
  expandedMap.value = [];
  showContextText.value = [];
  showPostprocessText.value = [];
  expandedPostprocessMap.value = [];
};
const checkTextOverflow = () => {
  nextTick(() => {
    groundTruthRefs.value.forEach((el, index) => {
      if (el) {
        showContextText.value[index] = el.scrollHeight > 44;
      }
    });
    postprocessRefs.value.forEach((el, index) => {
      if (el) {
        showPostprocessText.value[index] = el.scrollHeight > 44;
      }
    });
  });
};

const queryStageResults = async () => {
  const data: any = await getResultsByStage("postprocessing");

  Object.assign(allResult, data);
  handleResultsBuyCurrentPipeline();
};
const handleResultsBuyCurrentPipeline = () => {
  resultsData.value = [].concat(allResult[activePipelineId.value!]?.results);
  getCurrentQuery();
};
const queryStagePipelines = async () => {
  const data: any = await getStagePipelines("postprocessing");
  pipelineList.value = data.flat().map((item: any) => ({
    pipeline_id: item.pipeline_id,
    top_n: item.targets["postprocessor.reranker.top_n"],
  }));

  queryPipelinesRecall();
};
const queryPipelinesRecall = async () => {
  const data: any = await getMetricsByStage("postprocessing");

  pipelineList.value = pipelineList.value.map((item) => ({
    ...item,
    ...data[item.pipeline_id.toString()],
  }));

  activePipelineId.value = pipelineList.value.reduce((max, current) => {
    return current.postprocessing_recall_rate > max.postprocessing_recall_rate
      ? current
      : max;
  })?.pipeline_id;

  handleResultsBuyCurrentPipeline();
};
const handleUpdateId = (value: number) => {
  if (value) {
    currentQueryId.value = value;
    keywords.value = "";
    getCurrentQuery();
  }
};
const handleSwitchQuery = () => {
  isInit.value = false;
};
const clearTimers = () => {
  Object.values(timers).forEach((timerId: any) => {
    clearInterval(timerId);
  });
};
watch(
  () => currentQueryId.value,
  async () => {
    getCurrentQuery();
  },
  { immediate: false }
);
onMounted(async () => {
  await handlePostprocessRun();
  scrollContainer = document.querySelector(".layout-main");
  window.addEventListener("resize", checkTextOverflow);
});
onUnmounted(() => {
  clearTimers();
});
</script>

<style scoped lang="less">
.postprocess-container {
  padding-bottom: 64px;
  width: 100%;
  display: flex;

  .main-wrap {
    flex: 1;
    padding-bottom: 24px;
  }
  .title-wrap {
    font-size: 16px;
    font-weight: 600;
    color: var(--font-main-color);
    margin-bottom: 16px;
  }
  .tuner-wrap {
    width: 75%;
    margin: 0 auto;
    min-width: 600px;
    padding: 12px 0;
    min-width: 600px;
    :deep(.intel-steps) {
      justify-content: center;
      .intel-steps-item-tail::after {
        height: 2px;
        background: var(--color-primary-tip) !important;
      }
      .intel-steps-item-content {
        margin-top: 0;
        .intel-steps-item-title {
          color: var(--font-main-color);
        }
      }
    }
    .icon-wrap {
      .vertical-center;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      background-color: var(--color-deep-primaryBg);
      border: 1px solid var(--color-primaryBg);
      .icon-loading1 {
        color: var(--color-primary) !important;
        animation: spin 3s linear infinite;
      }
      &.icon-done {
        background-color: var(--color-success);
        border: 1px solid var(--color-switch-theme);
        .icon-copy-success {
          color: var(--color-white) !important;
        }
      }
    }
  }
  .warring-tip {
    border: 1px solid var(--border-warning);
    border-left: 3px solid var(--color-second-warning);
    background-color: var(--color-warningBg);
    color: var(--color-second-warning);
    padding: 8px 12px;
    border-radius: 0 4px 4px 0;
    margin-bottom: 12px;
    font-size: 12px;
    .flex-left;
    gap: 4px;
  }
  .chart-container {
    padding: 20px;
    background-color: var(--bg-card-color);
    border-radius: 6px;
    .chart-line {
      height: 300px;
      width: 95%;
      margin: 0 3%;
    }
    .rate-wrap {
      position: relative;
      .state-wrap {
        position: absolute;
        top: -5px;
        right: -40px;
        background: var(--color-success);
        color: var(--bg-content-color);
        padding: 2px 27px;
        font-size: 14px;
        font-size: 12px;
        transform: rotate(45deg) scale(0.7);
        .vertical-center;
      }
    }
  }
  .suggestion-wrap {
    display: none;
    background-color: var(--color-primaryBg);
    padding: 16px 12px;
    border-left: 4px solid var(--color-primary-tip);
    margin: 16px 0;
    color: var(--color-primary-second);
  }
  .select-wrap {
    .flex-left;
    gap: 12px;
    font-weight: 600;
    font-size: 15px;
    margin-top: 12px;
    .option-wrap {
      font-size: 13px;
      padding: 8px 20px;
      background-color: var(--bg-content-color);
      border: 1px solid var(--border-main-color);
      border-radius: 4px;
      cursor: pointer;
      gap: 4px;
      .vertical-center;
      &:hover {
        border: 1px solid var(--color-primary-second);
        background-color: var(--color-primaryBg);
      }
      &.is-active {
        color: var(--color-white);
        background-color: var(--color-primary-second);
        border: 1px solid var(--color-primary-second);
      }
    }
  }
  .ground-truth {
    margin-top: 16px;
    padding: 0 12px 20px 12px;
    border-radius: 6px;
    background-color: var(--bg-content-color);
    .contexts-container {
      background-color: var(--color-second-primaryBg);
      border: 1px solid var(--border-primary);
      border-radius: 8px;
      padding: 20px;
      .top-wrap {
        margin-bottom: 8px;
        .intel-tag-success {
          margin-left: 8px;
        }
        .file-name {
          font-size: 13px;
          font-weight: 600;
          color: var(--font-main-color);
        }
        .flex-between;
      }
      .context-wrap {
        border-radius: 6px;
        width: 100%;
        border: 1px solid var(--border-main-color);
        padding: 20px;
        margin-top: 16px;
        display: flex;
        gap: 12px;
        position: relative;
        background-color: var(--bg-content-color);
        .card-shadow;
        :deep(.intel-ribbon-wrapper) {
          position: absolute;
          right: 0;
          top: 1px;
        }
        .id-wrap {
          width: 32px;
          height: 32px;
          border-radius: 2px;
          background-color: var(--color-primaryBg);
          color: var(--color-primary-second);
          .vertical-center;
        }
        .content-wrap {
          flex: 1;
          .top-wrap {
            .flex-between;
            padding-right: 12px;
          }
          .text-wrapper {
            position: relative;
            margin-top: 12px;
            .text-content {
              display: -webkit-box;
              -webkit-line-clamp: 2;
              -webkit-box-orient: vertical;
              .word-wrap;
              &.ellipsis {
                overflow: hidden;
              }
              &.expanded {
                display: block;
              }
            }
            .expand-link {
              .flex-end;
              gap: 4px;
              font-size: 12px;
              color: var(--color-primary-second);
              cursor: pointer;
              position: relative;
              bottom: -4px;
              &:hover {
                color: var(--color-primary-tip);
              }
            }
          }
        }
        .hit-wrap {
          position: absolute;
          right: 20px;
          top: 8px;
          .vertical-center;
          .hit-item {
            .flex-column;
            align-items: center;
            color: var(--font-tip-color);
            .hit-icon {
              .vertical-center;
              height: 24px;
              width: 24px;
              border-radius: 50%;
              font-size: 12px;
              background-color: var(--border-main-color);
              color: var(--font-info-color);
            }
            &.active-hit {
              color: var(--font-main-color);
              .hit-icon {
                .vertical-center;
                background-color: var(--color-primary-second);
                color: var(--color-white);
              }
            }
          }
          .line-wrap {
            width: 48px;
            height: 2px;
            margin: 24px 12px 0 12px;
            background-color: var(--color-primary-second);
          }
        }
      }
    }
    .query-item {
      padding: 20px 0 0 12px;
    }
    :deep(.intel-affix) {
      background-color: var(--bg-content-color);
      .query-item {
        padding: 20px 20px 0 20px;
      }
    }
  }
  .postprocess-wrap {
    background-color: var(--color-second-successBg) !important;
    border: 1px solid var(--border-success) !important;
    color: var(--font-info-color) !important;
    .id-wrap {
      background-color: var(--color-second-successBg) !important;
      color: var(--color-success) !important;
    }
  }
  .search-wrap {
    position: relative;
    top: -8px;
    width: 220px;
    text-align: end;
  }
}
</style>
