<template>
  <div class="results-container">
    <div class="content-container">
      <div class="title-wrap">{{ $t("results.rating") }}</div>
      <v-chart class="chart-bar" :option="barChartOption" autoresize />
    </div>
    <div class="content-container">
      <div class="title-wrap">{{ $t("common.configuration") }}</div>
      <div
        class="pipeline-wrap"
        v-for="(item, index) in promptDetail"
        :key="item.id"
      >
        <div class="left-wrap">
          <div class="icon-wrap">
            <SvgIcon
              name="icon-prompt"
              :size="24"
              :style="{ color: 'var(--color-primary-tip)' }"
            />
          </div>
          <div>
            <div class="title">
              {{
                item.id === basePipeline
                  ? $t("common.original")
                  : `${$t("prompt.title")} ${index}`
              }}
            </div>
            <div class="des">
              <span>{{ $t("results.name") }}: {{ item.name }}</span>
              <span>{{ $t("results.id") }}: {{ item.id }}</span>
            </div>
          </div>
        </div>
        <div class="right-wrap">
          <a-tooltip placement="top" :title="$t('results.update')">
            <span class="icon-style" @click="handleSync(item.id)">
              <SvgIcon name="icon-sync" /> </span
          ></a-tooltip>
          <a-tooltip placement="top" :title="$t('results.detail')">
            <span class="icon-style" @click="handleView(item)">
              <EyeFilled /></span
          ></a-tooltip>
          <a-tooltip placement="top" :title="$t('results.download')"
            ><span class="icon-style" @click="handleDownload(item.id)">
              <SvgIcon name="icon-download" inherit /></span
          ></a-tooltip>
        </div>
      </div>
    </div>
    <div class="footer-container">
      <a-button type="primary" ghost @click="handleBack">
        <ArrowLeftOutlined />
        {{ $t("common.back") }}
      </a-button>
      <div>
        <a-button type="primary" @click="handleRetry">
          {{ $t("common.retry") }}
          <SyncOutlined />
        </a-button>
        <a-button type="primary" @click="handleExit">
          {{ $t("common.exit") }}
          <LogoutOutlined />
        </a-button>
      </div>
    </div>
    <!-- detailDrawer -->
    <DetailDrawer
      v-if="detailDrawer.visible"
      :drawer-data="detailDrawer.data"
      @close="detailDrawer.visible = false"
    />
  </div>
</template>

<script lang="ts" setup name="Results">
import { ref, reactive, onMounted } from "vue";
import { DetailDrawer } from "./index";
import { BarChart } from "echarts/charts";
import {
  exportPipelineUrl,
  requestPipelineSync,
  requesStageReset,
  getResultsByPipelineId,
  getPipelineDetailById,
  getResultsByStage,
} from "@/api/ragPilot";
import {
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  GridComponent,
} from "echarts/components";
import VChart from "vue-echarts";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import {
  EyeFilled,
  ArrowLeftOutlined,
  SyncOutlined,
  LogoutOutlined,
} from "@ant-design/icons-vue";
import SvgIcon from "@/components/SvgIcon.vue";
import router from "@/router";
import { Modal } from "ant-design-vue";
import { ResultOut } from "../type";
import { Local } from "@/utils/storage";
import { pipelineAppStore } from "@/store/pipeline";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const pipelineStore = pipelineAppStore();

echarts.use([
  CanvasRenderer,
  BarChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);
const emit = defineEmits(["search", "close"]);

const promptList = ref<string[]>();
const promptDetail = ref<EmptyArrayType>();
const stageList = ref<string[]>(["retrieval", "postprocessing", "generation"]);
const basePipeline = ref<number | null>();
const baseResults = ref<ResultOut[]>([]);
const chatMap = reactive<EmptyObjectType>({});
const detailDrawer = reactive<DialogType>({
  visible: false,
  data: {},
});
const colorList = ["#22C55E", "#507AFC", "#FAC858", "#93BEFF"];

const barChartOption = computed(() => {
  const chatKeys = Object.keys(chatMap);
  const seriesData = [
    {
      name: t("common.original"),
      type: "bar",
      data: baseResults.value?.map(
        (item) => item?.metadata?.answer_relevancy ?? 0
      ),
      barStyle: { color: "#9E87FF" },
      itemStyle: { color: "#9E87FF", borderColor: "#9E87FF" },
    },
  ];
  const legendData = [t("common.original")];

  chatKeys.forEach((key, index) => {
    const color = colorList[index % colorList.length];
    seriesData.push({
      name: handlelegend(index),
      type: "bar",
      data: chatMap[key].results.map(
        (item: any) => item?.metadata.answer_relevancy ?? 0
      ),
      barStyle: { color },
      itemStyle: { color, borderColor: color },
    });
    legendData.push(handlelegend(index));
  });

  const xAxisDataLength =
    chatKeys.length > 0 ? chatMap[chatKeys[0]].results.length : 0;
  const xAxisData = Array.from({ length: xAxisDataLength }, (_, i) => i + 1);

  return {
    color: colorList,
    grid: { top: 50, right: 20, bottom: 50, left: 50 },
    legend: {
      data: legendData,
      type: "scroll",
    },
    xAxis: {
      name: t("common.query"),
      nameLocation: "center",
      nameGap: 28,
      nameTextStyle: {
        fontWeight: "bold",
        fontSize: "14",
      },
      boundaryGap: [0, 0.01],
      data: xAxisData,
    },
    yAxis: [
      {
        type: "value",
        min: 0,
        max: 5,
        interval: 1,
        splitbar: {
          show: true,
        },
        axisLabel: {
          formatter: "{value}",
        },
      },
    ],
    series: seriesData,
  };
});
const handlelegend = (index: number) => {
  return `${t("prompt.title")} ${index + 1}`;
};
const handleSync = (id: number) => {
  requestPipelineSync(id);
};
const handleView = (row: any) => {
  detailDrawer.data = row;
  detailDrawer.visible = true;
};
const handleDownload = (id: number) => {
  const link = document.createElement("a");

  link.href = exportPipelineUrl(id);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};
const handleReset = async () => {
  try {
    const promises = stageList.value.map((stage) => requesStageReset(stage));
    await Promise.all(promises);
    pipelineStore.setPipeline("");
  } catch (err) {
    console.log(err);
  }
};
const queryResultsByStage = async () => {
  basePipeline.value = Local.get("pipelineInfo")?.basePipeline ?? "";
  const baseData: any = await getResultsByPipelineId(basePipeline.value!);
  baseResults.value = [].concat(baseData.results);

  const data: any = await getResultsByStage("generation");
  Object.assign(chatMap, data, {});

  promptList.value = [...[basePipeline.value], ...Object.keys(data)];
  queryPipelinesDetail();
};

const queryPipelinesDetail = async () => {
  try {
    const promises = promptList.value?.map((id) => getPipelineDetailById(id));
    const data: any = await Promise.all(promises!);

    promptDetail.value = [].concat(data);
  } catch (err) {
    console.log(err);
  }
};
const handleRetry = () => {
  Modal.confirm({
    title: t("common.prompt"),
    content: t("results.retryTip"),
    okText: t("common.confirm"),
    async onOk() {
      await handleReset();
      router.push({ name: "Rating" });
    },
  });
};
const handleBack = () => {
  router.push({ name: "Generation" });
};
const handleExit = () => {
  Modal.confirm({
    title: t("common.prompt"),
    content: t("common.exitTip"),
    okText: t("common.confirm"),
    async onOk() {
      await handleReset();
      router.push({ name: "Home" });
    },
  });
};
onMounted(async () => {
  queryResultsByStage();
});
</script>

<style lang="less">
.results-container {
  width: 100%;
  padding-bottom: 84px;
  .content-container {
    background-color: var(--bg-content-color);
    margin-top: 16px;
    padding: 20px;
    border-radius: 8px;
  }
  .chart-bar {
    height: 300px;
    width: 100%;
  }
  .title-wrap {
    font-size: 16px;
    color: var(--font-main-color);
    font-weight: 600;
    margin-bottom: 12px;
  }
  .pipeline-wrap {
    background-color: var(--bg-main-color);
    border-radius: 6px;
    padding: 12px;
    margin-top: 12px;
    .flex-between;
    .left-wrap {
      .flex-left;
      flex: 1;
      gap: 6px;
      font-weight: 600;
      color: var(--font-main-color);
      .icon-wrap {
        background-color: var(--color-primaryBg);
        border-radius: 6px;
        width: 42px;
        height: 42px;
        .vertical-center;
      }
      .des {
        font-size: 12px;
        color: var(--font-tip-color);
        font-weight: 500;
        margin-top: 8px;
        span {
          margin-right: 16px;
        }
      }
    }
    .right-wrap {
      .flex-end;
      gap: 8px;
      .icon-style {
        font-size: 16px;
        color: var(--font-info-color);
        cursor: pointer;
        &:hover {
          color: var(--color-primary);
        }
      }
    }
  }
}
</style>
