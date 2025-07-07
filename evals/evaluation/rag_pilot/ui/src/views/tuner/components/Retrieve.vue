<template>
  <div class="retrieve-container">
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
              {{ transformTunerName(menu.name) }}
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
      <div class="table-wrap">
        <div class="title-wrap">{{ $t("common.configuration") }}</div>
        <a-table
          :columns="tableColumns"
          :data-source="tableList"
          :pagination="false"
          bordered
          showSorterTooltip
          size="middle"
          :scroll="{ x: 760, y: 320 }"
          :row-class-name="setSelectedClass"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.dataIndex === 'id'">
              <div class="rate-wrap">
                <span class="state-wrap" v-if="record.isSelected">{{
                  $t("common.selected")
                }}</span>
                {{ record.id }}
              </div>
            </template>
            <template v-if="column.dataIndex === 'retrieval_recall_rate'">
              {{ formatPercentage(record.retrieval_recall_rate ?? 0) }}
            </template>
          </template>
        </a-table>
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
                    :placeholder="$t('retriever.search')"
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
                {{ $t("retriever.recall") }}:
                {{ recallRate }}
              </a-tag>
            </div>
            <a-tag color="processing"
              >{{ $t("common.total") }}: {{ contextsTotal }}</a-tag
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
                <span
                  v-if="context.metadata?.retrieval?.length && !showHit[index]"
                  class="link-wrap"
                  @click="toggleContext(index)"
                >
                  <EyeOutlined />
                  {{ $t("retriever.showHit") }}
                </span>
              </div>

              <div class="text-wrapper" ref="groundTruthRefs">
                <div
                  :class="{
                    'text-content ': true,
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
              <transition name="expand-fade">
                <div v-if="context?.hitRetrieveContexts?.length">
                  <div class="hit-context" v-if="showHit[index]">
                    <div class="title-wrap">
                      {{ $t("retriever.retrieved") }}
                    </div>
                    <div
                      class="hit-item"
                      v-for="(item, k) in context.hitRetrieveContexts"
                      :key="item.context_idx"
                    >
                      <a-divider v-if="k" />
                      <div class="top-wrap">
                        <span class="file-name">
                          <a-tag :bordered="false">
                            {{ context.file_name }}
                          </a-tag></span
                        >
                      </div>
                      <div
                        class="hit-text word-wrap"
                        v-html="marked(item.text!)"
                      ></div>
                    </div>
                  </div>
                  <div class="footer-wrap" v-if="showHit[index]">
                    <span class="link-wrap" @click="toggleContext(index)">
                      <EyeInvisibleOutlined />
                      {{ $t("retriever.hideHit") }}
                    </span>
                  </div>
                </div></transition
              >
            </div>
            <a-badge-ribbon
              v-if="context.metadata?.retrieval?.length"
              text="Hit"
              color="var(--color-primary-second)"
            ></a-badge-ribbon>
          </div>
        </div>
        <div id="Retrieval" class="contexts-container retrieval-wrap mt-16">
          <div class="top-wrap">
            <div class="left-wrap">
              <span class="title-wrap"> {{ $t("retriever.chunk") }}</span>
            </div>
            <a-tag color="success"
              >{{ $t("common.total") }}: {{ retrievalTotal }}</a-tag
            >
          </div>
          <div
            class="context-wrap"
            v-for="(retrieval, k) in retrievalSearchData"
            :key="retrieval.context_idx"
          >
            <div class="id-wrap">{{ k + 1 }}</div>
            <div class="content-wrap">
              <div class="top-wrap">
                <span class="file-name">
                  <a-tag :bordered="false">
                    {{ retrieval.file_name }}
                  </a-tag></span
                >
              </div>
              <div class="text-wrapper" ref="retrievalRefs">
                <div
                  :class="{
                    'text-content': true,
                    ellipsis: showRetrievalText[k],
                    expanded: expandedRetrievalMap[k],
                  }"
                  v-html="marked(retrieval.highlightedText!)"
                ></div>
                <p
                  v-if="showRetrievalText[k]"
                  @click="toggleRetrievalExpand(k)"
                  class="expand-link"
                >
                  {{
                    expandedRetrievalMap[k]
                      ? $t("common.collapse")
                      : $t("common.expand")
                  }}
                  <UpOutlined v-if="expandedRetrievalMap[k]" />
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
      <a-button type="primary" :disabled="!tunerDone" @click="handleNext">
        {{ $t("common.next") }}
        <ArrowRightOutlined />
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup name="Retrieve">
import { ref, reactive, computed, onMounted } from "vue";
import { QueryMenu } from "./index";
import {
  requesStageRun,
  getPipelineDetailById,
  getResultsByPipelineId,
  getStagePipelines,
  getMetricsByStage,
  getTunerStatus,
  getMetricsByPipelineId,
  getActivePipeline,
} from "@/api/ragPilot";
import {
  EyeOutlined,
  EyeInvisibleOutlined,
  UpOutlined,
  DownOutlined,
  ArrowLeftOutlined,
  ArrowRightOutlined,
  SearchOutlined,
  ExclamationCircleFilled,
} from "@ant-design/icons-vue";
import { formatTextStrict, formatPercentage } from "@/utils/common";
import { ResultOut } from "../type";
import CustomRenderer from "@/utils/customRenderer";
import { marked } from "marked";
import { transformTunerName } from "@/utils/common";
import router from "@/router";
import { useI18n } from "vue-i18n";
import { Local } from "@/utils/storage";

const { t } = useI18n();

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});

const basePipeline = ref<number | null>();
const isInit = ref<boolean>(true);
let scrollContainer: any = null;
const bestPipelineId = ref<number>();
const resultsData = ref<ResultOut[]>([]);
const timers = reactive<any>({});
const tableList = ref<EmptyArrayType>([]);
let tunerList = ref<EmptyArrayType>([]);
const currentQuery = reactive<ResultOut>({});
const currentQueryId = ref<number>();
const keywords = ref<string>("");
const tableColumns = ref<TableColumns[]>([
  {
    title: "Pipeline ID",
    dataIndex: "id",
    width: 300,
    fixed: "left",
  },
  {
    title: t("retriever.configuration"),
    dataIndex: "configuration",
    children: [
      {
        title: "Recall rate",
        dataIndex: "retrieval_recall_rate",
        fixed: "right",
      },
    ],
  },
]);
const showHit = ref<boolean[]>([]);
const showContextText = ref<boolean[]>([]);
const expandedMap = ref<boolean[]>([]);
const showRetrievalText = ref<boolean[]>([]);
const expandedRetrievalMap = ref<boolean[]>([]);

const tunerDone = computed(() => {
  const statusList = ["completed", "inactive"];
  return tunerList.value?.every((item) => statusList.includes(item.status));
});

const setSelectedClass = (record: any, index: number) => {
  if (record.isSelected) {
    return "is-selected";
  }
};
const getScrollContainer = () =>
  document.querySelector(".layout-main") as HTMLElement;

const retrievalSearchData = computed(() => {
  const { retrieval_contexts = [] } = currentQuery;
  const kw = keywords.value.trim();
  if (!kw) {
    return retrieval_contexts.map((item) => ({
      ...item,
      highlightedText: item.text,
    }));
  }
  const escapeRegExp = (text: string) =>
    text.replace(/[-\/\\^$*+?.()|[\]{}]/g, "\\$&");
  const safeKw = escapeRegExp(kw);
  const regex = new RegExp(`(${safeKw})`, "gi");
  return retrieval_contexts.map((item) => ({
    ...item,
    highlightedText: item.text.replace(
      regex,
      "<mark class='highlighted'>$1</mark>"
    ),
  }));
});
const handleRetrieveRun = async () => {
  const data: any = await requesStageRun("retrieval");
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

    queryStagePipelines();
    clearInterval(timers[tunerName]);
    delete timers[tunerName];
    if (tunerDone.value) {
      queryActivePipelineId();
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
const getCurrentQuery = () => {
  let queryData: any =
    resultsData.value.find((item) => item?.query_id === currentQueryId.value) ||
    {};

  const { retrieval_contexts } = queryData;
  queryData.gt_contexts?.forEach((item: any) => {
    item.hitRetrieveContexts = retrieval_contexts?.filter((k: any) =>
      item.metadata.retrieval?.includes(k.context_idx)
    );
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
const toggleExpand = (index: number) => {
  expandedMap.value[index] = !expandedMap.value[index];
};
const toggleRetrievalExpand = (index: number) => {
  expandedRetrievalMap.value[index] = !expandedRetrievalMap.value[index];
};

const groundTruthRefs = ref<Array<HTMLElement | null>>([]);
const retrievalRefs = ref<Array<HTMLElement | null>>([]);
const contextsTotal = computed(() => {
  return currentQuery.gt_contexts?.length || 0;
});
const retrievalTotal = computed(() => {
  return currentQuery.retrieval_contexts?.length || 0;
});
const recallRate = computed(() => {
  const { gt_contexts = [] } = currentQuery;
  const count = gt_contexts.filter(
    (item) => item.metadata?.retrieval?.length
  ).length;
  return `${formatPercentage(count / contextsTotal.value)}(${count}/${
    contextsTotal.value
  })`;
});

const toggleContext = (index: number) => {
  showHit.value[index] = !showHit.value[index];
};
const handleMapReset = () => {
  showHit.value = [];
  expandedMap.value = [];
  showContextText.value = [];
  showRetrievalText.value = [];
  expandedRetrievalMap.value = [];
};
const checkTextOverflow = () => {
  nextTick(() => {
    groundTruthRefs.value.forEach((el, index) => {
      if (el) {
        showContextText.value[index] = el.scrollHeight > 44;
      }
    });
    retrievalRefs.value.forEach((el, index) => {
      if (el) {
        showRetrievalText.value[index] = el.scrollHeight > 44;
      }
    });
  });
};

const queryStagePipelines = async () => {
  basePipeline.value = Local.get("pipelineInfo")?.basePipeline;
  const data: any = await getStagePipelines("retrieval");
  const allPipelineItems = Object.values(data).flat();
  const pipelineIds = [
    ...new Set(allPipelineItems.flatMap((item: any) => [item.pipeline_id])),
  ];
  pipelineIds.push(basePipeline.value);
  const targetKeys = allPipelineItems.flatMap((item: any) => {
    return Object.keys(item.targets || {}).map((fullKey) => {
      const parts = fullKey.split(".");
      return {
        name: parts[parts.length - 1],
        key:
          parts.length > 2
            ? [parts.slice(0, 1), parts.slice(-1)].flat()
            : parts,
      };
    });
  });
  const uniqueTargetKeys = Array.from(
    new Map(targetKeys.map((item) => [item.name, item])).values()
  );
  queryPipelinesConfig(pipelineIds);
  inItTableColumns(uniqueTargetKeys);
};
const queryPipelinesConfig = async (pipelines: EmptyArrayType) => {
  try {
    const promises = pipelines.map((id) => getPipelineDetailById(id));
    const responses: any = await Promise.all(promises);
    const validResponses = responses.filter(
      (response: any) => response != null
    );

    tableList.value = [].concat(...validResponses);

    if (tunerDone.value) {
      queryPipelinesRecall();
    }
  } catch (err) {
    console.log(err);
  }
};
const queryPipelinesRecall = async () => {
  try {
    const [stageMetrics, baseMetrics]: [any, any] = await Promise.all([
      getMetricsByStage("retrieval"),
      getMetricsByPipelineId(basePipeline.value!),
    ]);
    tableList.value = tableList.value.map((item, index) => {
      if (item.id === basePipeline.value) {
        return {
          ...item,
          ...baseMetrics,
        };
      } else {
        return {
          ...item,
          ...(stageMetrics[item.id.toString()]
            ? { ...stageMetrics[item.id.toString()] }
            : {}),
        };
      }
    });
    handleSelectedPipeline();
  } catch (err) {
    console.log(err);
  }
};

const handleSelectedPipeline = () => {
  const index = tableList.value.findIndex(
    (item) => item.id === bestPipelineId.value
  );
  if (index === -1) return;

  const item = { ...tableList.value[index], isSelected: true };
  tableList.value.splice(index, 1);
  tableList.value.unshift(item);
};

const inItTableColumns = (targets: EmptyArrayType) => {
  targets.forEach((target) => {
    tableColumns.value.forEach((column: TableColumns, index: number) => {
      if (column.dataIndex === "configuration") {
        if (
          !tableColumns.value[index].children.some(
            (item: any) => item.title === formatTextStrict(target.name)
          )
        ) {
          tableColumns.value[index].children.unshift({
            title: formatTextStrict(target.name),
            dataIndex: target.key,
          });
        }
      }
    });
  });
};

const queryActivePipelineId = async () => {
  const pipeline_id: any = await getActivePipeline();
  bestPipelineId.value = pipeline_id;

  getQuerysResult();
};
const getQuerysResult = async () => {
  const data: any = await getResultsByPipelineId(bestPipelineId.value!);

  resultsData.value = [].concat(data?.results);
  getCurrentQuery();
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
const handleSearch = async () => {
  const element = document.getElementById("Retrieval");

  if (element) {
    const offsetPosition = element.offsetTop - 140;

    scrollContainer?.scrollTo({
      top: offsetPosition,
      behavior: "smooth",
    });
  }
  const { retrieval_contexts = [] } = currentQuery;
  expandedRetrievalMap.value = retrieval_contexts.map(() => true);
};
const handleBack = async () => {
  router.push({ name: "Rating" });
};
const handleNext = async () => {
  router.push({ name: "Postprocess" });
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
onMounted(async () => {
  handleRetrieveRun();
  scrollContainer = document.querySelector(".layout-main");
  window.addEventListener("resize", checkTextOverflow);
});
onUnmounted(() => {
  clearTimers();
});
</script>

<style scoped lang="less">
.retrieve-container {
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
    :deep(.intel-steps) {
      .intel-steps-item-tail::after {
        height: 2px;
        background: var(--color-primary-tip) !important;
      }
      .intel-steps-item-content {
        margin-top: 0;
        .intel-steps-item-title {
          color: var(--font-main-color);
          white-space: nowrap;
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
      &.icon-warring {
        background-color: var(--color-infoBg);
        border: 1px solid var(--border-info);
        .icon-copy-success {
          color: var(--color-info) !important;
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
  .table-wrap {
    padding: 20px;
    background-color: var(--bg-card-color);
    border-radius: 6px;
    :deep(.intel-table) {
      .is-selected {
        .intel-table-cell {
          background-color: var(--color-successBg);
          overflow: hidden;
        }
      }
    }
    .rate-wrap {
      position: relative;
      white-space: nowrap;
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
  .ground-truth {
    margin-top: 20px;
    padding-bottom: 20px;
    border-radius: 6px;
    background-color: var(--bg-content-color);

    .contexts-container {
      background-color: var(--color-second-primaryBg);
      border: 1px solid var(--border-primary);
      border-radius: 8px;
      padding: 20px;
      margin: 16px 12px 0 12px;
      .top-wrap {
        margin-bottom: 8px;
        .flex-between;
        .intel-tag-success {
          margin-left: 8px;
        }
        .file-name {
          font-size: 13px;
          font-weight: 600;
          color: var(--font-main-color);
        }
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
              &:hover {
                color: var(--color-primary-tip);
              }
            }
          }

          .hit-context {
            background-color: var(--bg-main-color);
            border-radius: 8px;
            padding: 12px;
            margin-top: 16px;
            border: 1px solid var(--border-main-color);
            :deep(.intel-divider-horizontal) {
              margin: 8px 0;
            }
            .hit-text {
              word-wrap: normal;
            }
          }
          .footer-wrap {
            .flex-end;
            margin-top: 12px;
          }
        }
        .link-wrap {
          color: var(--color-primary);
          cursor: pointer;
          display: inline-flex;
          gap: 4px;
          &:hover {
            color: var(--color-primary-hover);
          }
        }
      }
    }
    .query-item {
      padding: 20px 12px 0 12px;
    }
    :deep(.intel-affix) {
      background-color: var(--bg-content-color);
      .query-item {
        padding: 20px 20px 0 20px;
      }
    }
  }
  .retrieval-wrap {
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
