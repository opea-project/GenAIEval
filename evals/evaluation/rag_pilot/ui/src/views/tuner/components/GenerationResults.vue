<template>
  <div class="generation-results-container">
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
      <TunerLoading :visible="loading" />
      <template v-if="resultsData.length">
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
                <div class="id-wrap">#{{ item.query_id }}</div>
                <div class="title-wrap">{{ item.query }}</div>
              </div>
              <div class="right-wrap">
                <a-tabs
                  v-model:activeKey="activeIdMap[index]"
                  type="card"
                  size="small"
                >
                  <a-tab-pane
                    v-for="(tab, k) in promptList"
                    :key="tab"
                    :tab="`${$t('prompt.title')} ${k + 1}`"
                  ></a-tab-pane>
                </a-tabs>
              </div>
            </div>
            <div class="results-wrap">
              <div class="common-wrap original-wrap">
                <div class="rate-wrap disabled">
                  <a-rate
                    v-model:value="item.base!.metadata!.answer_relevancy"
                    disabled
                  />
                </div>
                <span class="type-wrap">{{ $t("common.original") }}</span>
                <span
                  class="marked-wrap"
                  v-html="marked(item.base?.response!)"
                ></span>
              </div>
              <div class="common-wrap final-wrap">
                <template v-if="item[activeIdMap[index]]">
                  <div class="rate-wrap">
                    <a-rate
                      v-model:value="item[activeIdMap[index]].metadata!.answer_relevancy"
                    />
                  </div>
                  <span class="type-wrap">{{ $t("common.final") }}</span>
                  <span
                    class="marked-wrap"
                    v-html="marked(item[activeIdMap[index]].response)"
                  ></span
                ></template>
                <div v-else class="loading-wrap">
                  <a-spin tip="Loading"> </a-spin>
                </div>
              </div>
            </div>
          </div></div
      ></template>
    </div>
    <div class="footer-container">
      <a-button type="primary" ghost @click="handleBack">
        <ArrowLeftOutlined />
        {{ $t("common.back") }}</a-button
      >
      <a-button type="primary" @click="handleNext" :disabled="!allRated">
        {{ $t("common.next") }}
        <ArrowRightOutlined />
      </a-button>
    </div>
  </div>
</template>

<script lang="ts" setup name="GenerationResults">
import { ref, computed, onMounted } from "vue";
import { QueryMenu, TunerLoading } from "./index";
import { requestResultsMetrics } from "@/api/ragPilot";
import { ResultOut } from "../type";
import {
  StarFilled,
  ArrowRightOutlined,
  ArrowLeftOutlined,
} from "@ant-design/icons-vue";
import { debounce } from "lodash-es";
import { marked } from "marked";
import CustomRenderer from "@/utils/customRenderer";
import router from "@/router";
import _ from "lodash";

marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});
const props = defineProps({
  pipelines: {
    type: Array,
    required: true,
    default: () => [],
  },
  results: {
    type: Array,
    required: true,
    default: () => [],
  },
  baseResult: {
    type: Array,
    required: true,
    default: () => [],
  },
});

const emit = defineEmits(["back"]);

const promptList = ref<EmptyArrayType>(props.pipelines);
const activeIdMap = ref<EmptyArrayType>([]);
const resultsData = ref<ResultOut[]>([]);
const headerHeight = 46;
const sectionRefs = ref<HTMLElement[]>([]);
let scrollContainer: any = null;
const activeSection = ref<number>();

const loading = computed(() => {
  return !resultsData.value?.length;
});
const rated = computed(() => {
  return resultsData.value?.reduce((count: number, item: any) => {
    const isActiveFound = promptList.value?.some(
      (key) => item[key]?.metadata?.answer_relevancy
    );
    return isActiveFound ? count + 1 : count;
  }, 0);
});
const allRated = computed(() => {
  return promptList.value.every((prompt) => {
    return resultsData.value.some((item) => {
      return item[prompt]?.metadata?.answer_relevancy > 0;
    });
  });
});
const maxRated = computed(() => {
  return resultsData.value?.length || 0;
});
const formatResults = async (results: any[]) => {
  if (!scrollContainer) return;
  const prevScrollTop = scrollContainer.scrollTop;
  const { baseResult = [], pipelines = [] } = props;

  if (!resultsData.value.length) {
    resultsData.value = [...baseResult];
  }

  const resultMap = new Map(results.map((item) => [item.query_id, item]));

  resultsData.value = resultsData.value.map((baseItem) => {
    const updateItem = resultMap.get(baseItem.query_id);
    if (!updateItem) return baseItem;

    const merged = { ...baseItem };

    pipelines.forEach((key: any) => {
      const val = baseItem[key];
      const shouldUpdate = val === undefined || val === null || val === "";
      if (shouldUpdate && updateItem[key] !== undefined) {
        merged[key] = updateItem[key];
      }
    });

    return merged;
  });
  const existingIds = new Set(resultsData.value.map((item) => item.query_id));
  const newItems = results.filter((item) => !existingIds.has(item.query_id));
  resultsData.value.push(...newItems);

  scrollContainer.scrollTop = prevScrollTop;
  handleScroll();
};

const formatFormParam = (key: string) => {
  return resultsData.value.map(({ query_id, [key]: response }) => {
    const answer_relevancy = response?.metadata?.answer_relevancy ?? 0;

    return {
      query_id,
      metadata: { answer_relevancy },
    };
  });
};

const handleNext = async () => {
  try {
    const promises = promptList.value.map((key) =>
      requestResultsMetrics(key, formatFormParam(key))
    );
    await Promise.all(promises);
    router.push({ name: "Results" });
  } catch (err) {
    console.log(err);
  }
};
const handleBack = async () => {
  emit("back");
};

const handleUpdateId = (value: number) => {
  if (value) handleScrollTo(value!);
};
const handleScrollTo = (id: number) => {
  const element = document.getElementById(id.toString());
  if (element) {
    const offsetPosition = element.offsetTop - headerHeight - 12;

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

watch(
  () => props.baseResult,
  (value) => {
    if (value.length) {
      resultsData.value = [].concat(value);
      activeIdMap.value = value.map(() => props.pipelines[0] ?? "") || [];
    }
  },
  { immediate: true }
);
watch(
  () => props.results,
  (value) => {
    if (value.length) {
      const results = _.cloneDeep(value);

      nextTick(() => formatResults(results));
    }
  },
  { immediate: true, deep: true }
);

onMounted(() => {
  scrollContainer = document.querySelector(".layout-main");
  if (scrollContainer) {
    scrollContainer.addEventListener("scroll", handleScroll);
    handleScroll();
  }
});
onUnmounted(() => {
  scrollContainer?.removeEventListener("scroll", handleScroll);
});
</script>

<style scoped lang="less">
.generation-results-container {
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
      border: 1px solid var(--color-second-primaryBg);
      background: var(--color-second-primaryBg);
      margin-top: 12px;
      width: 100%;
      &:hover {
        box-shadow: 0px 4px 8px 0px var(--bg-box-shadow);
      }
      .results-wrap {
        .flex-left;
        gap: 12px;
        .common-wrap {
          flex: 1;
          padding: 12px;
          position: relative;
          border-radius: 6px;
          height: 100%;
          .card-shadow;
          .type-wrap {
            position: absolute;
            right: -1px;
            top: -1px;
            border-radius: 0 6px 0 6px;
            padding: 0 3px;
            height: 20px;
            font-size: 12px;
            color: var(--color-white);
            .vertical-center;
          }
          &.original-wrap {
            background: linear-gradient(
              156deg,
              var(--color-purpleBg) -59%,
              var(--color-white) 159%
            );
            border: 1px solid var(--border-purple);
            .type-wrap {
              background-color: var(--color-purple);
            }
          }
          &.final-wrap {
            background: linear-gradient(
              154deg,
              var(--color-second-successBg) -51%,
              var(--color-white) 151%
            );
            border: 1px solid var(--border-success);
            .type-wrap {
              background-color: var(--color-success);
            }
          }
        }
      }
    }
    .query-wrap {
      gap: 0;
      .right-wrap {
        box-shadow: none;
        top: 0;
        padding: 0;
        background-color: transparent;
        max-width: 45%;
      }
      .rate-wrap {
        box-shadow: 0px 2px 4px 4px var(--bg-box-shadow);
        padding: 0 4px 4px 4px;
        display: inline-block;
        border-radius: 4px;
        position: relative;
        top: -4px;
      }
      .marked-wrap {
        word-wrap: break-word;
        word-break: break-all;
      }
    }
    :deep(.intel-tabs) {
      position: relative;
      bottom: -1px;
      z-index: 20;
      .intel-tabs-nav {
        margin: 0;
        &::before {
          display: none;
        }
        .intel-tabs-nav-wrap {
          justify-content: end;
        }
      }
      .intel-tabs-tab-active {
        background: linear-gradient(
          154deg,
          var(--color-second-successBg) -51%,
          var(--color-white) 151%
        );
        border: 1px solid var(--border-success);
        border-bottom: none;
      }
    }
    .loading-wrap {
      .vertical-center;
      height: 100%;
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
