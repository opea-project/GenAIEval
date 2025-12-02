<template>
  <a-drawer
    v-model:open="drawerVisible"
    :title="null"
    destroyOnClose
    :closable="false"
    placement="top"
    height="100%"
    :keyboard="false"
    :maskClosable="false"
    @close="handleClose"
    class="create-drawer"
  >
    <div class="enter-wrap">
      <div class="title-wrap">{{ $t("home.annotationAdd") }}</div>
      <div class="des-wrap">{{ $t("home.annotationDes") }}</div>
      <a-form
        :model="form"
        :rules="rules"
        name="postitem"
        ref="formRef"
        autocomplete="off"
        class="form-wrap"
        layout="vertical"
      >
        <div
          class="item-wrap"
          v-for="(item, index) in form.annotation"
          :key="index"
        >
          <div v-if="!item.isSubmit" class="query-index">Q{{ index + 1 }}</div>
          <div
            class="question-header"
            v-if="item.isSubmit"
            @click="toggleExpand(item)"
          >
            <span class="question-number">#{{ index + 1 }}</span>
            <span class="question-query"
              >{{ item.query }}
              <a-tooltip
                placement="top"
                arrow-point-at-center
                :title="$t('common.edit')"
                v-if="item.isPass"
              >
                <span class="edit-icon">
                  <EditOutlined @click.stop="handleQueryEdit(item)" />
                </span>
              </a-tooltip>
            </span>
            <component
              :is="item.collapse ? UpOutlined : DownOutlined"
              class="arrow-icon"
            />
          </div>
          <transition name="expand-fade">
            <div class="content-wrap" v-show="!item.collapse">
              <div class="warring-tip" v-if="item.isSubmit">
                <ExclamationCircleFilled />
                {{ $t(`home.${item.isPass ? "isEditDes" : "verifyDes"}`) }}
              </div>
              <a-form-item
                :name="['annotation', index, 'query']"
                :rules="rules.query"
                v-if="!item.isSubmit"
              >
                <template #label>
                  <div class="flex-between">
                    <span>{{ $t("home.form.label.query") }}</span>
                    <FormTooltip
                      icon="QuestionCircleOutlined"
                      :title="$t('home.form.tip.query')"
                    />
                  </div>
                </template>
                <a-textarea
                  v-model:value="item.query"
                  :placeholder="$t('home.form.placeholder.query')"
                  :auto-size="{ minRows: 1, maxRows: 2 }"
                />
              </a-form-item>
              <a-form-item
                :name="['annotation', index, 'contexts']"
                :rules="rules.contexts"
                class="gt-wrap"
              >
                <template #label>
                  <div class="flex-between">
                    <span>{{ $t("home.form.label.gt_context") }}</span>
                  </div>
                </template>
                <div
                  v-for="(context, k) in item.contexts"
                  :key="k"
                  class="item-wrap context-wrap"
                >
                  <span class="gt-index">{{ k + 1 }}</span>
                  <div class="flex-left">
                    <a-form-item
                      :name="['annotation', index, 'contexts', k, 'filename']"
                      :rules="rules.fileName"
                      class="flex-item"
                    >
                      <template #label>
                        <div class="flex-between">
                          <span>{{ $t("home.form.label.fileName") }}</span>
                          <FormTooltip
                            icon="QuestionCircleOutlined"
                            :title="$t('home.form.tip.fileName')"
                          />
                        </div>
                      </template>
                      <a-select
                        showSearch
                        v-model:value="context.filename"
                        :disabled="item.isPass"
                        :placeholder="$t('home.form.placeholder.file')"
                        @dropdownVisibleChange="handleFileVisible"
                      >
                        <a-select-option
                          v-for="item in fileList"
                          :key="item.file_name"
                          :value="item.file_name"
                          >{{ item.file_name }}</a-select-option
                        >
                      </a-select>
                    </a-form-item>
                    <a-form-item
                      :name="['annotation', index, 'contexts', k, 'text']"
                      :rules="rules.text"
                      class="flex-item"
                    >
                      <template #label>
                        <div class="flex-between">
                          <span>{{ $t("home.form.label.context") }}</span>
                          <FormTooltip
                            icon="QuestionCircleOutlined"
                            :title="$t('home.form.tip.context')"
                          />
                        </div>
                      </template>
                      <a-textarea
                        v-model:value="context.text"
                        :disabled="item.isPass"
                        :placeholder="$t('home.form.placeholder.context')"
                        :auto-size="{ minRows: 1, maxRows: 5 }"
                      />
                    </a-form-item>
                  </div>
                  <div class="flex-left">
                    <a-form-item
                      :name="['annotation', index, 'contexts', k, 'section']"
                      class="flex-item"
                    >
                      <template #label>
                        <div class="flex-between">
                          <span>{{ $t("home.form.label.section") }}</span>
                          <FormTooltip
                            icon="QuestionCircleOutlined"
                            :title="$t('home.form.tip.section')"
                          />
                        </div>
                      </template>
                      <a-input
                        v-model:value="context.section"
                        :disabled="item.isPass"
                        @change="handleSectionChange(context)"
                        :placeholder="$t('home.form.placeholder.section')"
                      />
                    </a-form-item>

                    <a-form-item
                      :name="['annotation', index, 'contexts', k, 'pages']"
                      class="flex-item"
                    >
                      <template #label>
                        <div class="flex-between">
                          <span>{{ $t("home.form.label.pages") }}</span>
                          <FormTooltip
                            icon="QuestionCircleOutlined"
                            :title="$t('home.form.tip.pages')"
                          />
                        </div>
                      </template>
                      <a-input
                        v-model:value="context.pages"
                        :disabled="item.isPass"
                        @change="handlePagesChange(context)"
                        :placeholder="$t('home.form.placeholder.pages')"
                      />
                    </a-form-item>
                  </div>
                  <div class="icon-wrap">
                    <a-tooltip
                      placement="topRight"
                      arrow-point-at-center
                      :title="$t('home.form.delContext')"
                      v-if="item.contexts?.length > 1"
                    >
                      <DeleteOutlined
                        @click="handleContextDelete(item.contexts, k)"
                      />
                    </a-tooltip>
                  </div>
                  <template
                    v-if="
                      !item.isPass &&
                      item.isSubmit &&
                      !context.isSelected &&
                      context.suggestions?.length
                    "
                  >
                    <div class="result-wrap">
                      <a-form-item-rest>
                        <a-radio-group
                          v-model:value="context.text"
                          @change="
                            (enevt:any) => handleSuggestionChange(context, enevt)
                          "
                        >
                          <a-radio
                            v-for="option in context.suggestions"
                            :key="option.node_id"
                            class="option-item"
                            :value="option.best_match_context"
                          >
                            <div class="radio-wrap">
                              <div class="flex-between">
                                <span>
                                  <span class="label-wrap"
                                    >{{ $t("home.bestContext") }}：</span
                                  >
                                  {{ option.best_match_context }}</span
                                >
                                <span>
                                  <span class="label-wrap">
                                    <a-tag color="success">
                                      {{ $t("home.matchScore") }}:
                                      {{
                                        formatPercentage(
                                          option.best_match_score
                                        )
                                      }}
                                    </a-tag>
                                  </span></span
                                >
                              </div>
                              <a-divider dashed />
                              <div
                                class="original-text"
                                v-html="marked(option.node_context)"
                              ></div>
                            </div>
                          </a-radio> </a-radio-group
                      ></a-form-item-rest></div
                  ></template>
                </div>
                <div
                  class="add-wrap"
                  v-if="!item.isPass"
                  @click="handleContextAdd(item.contexts)"
                >
                  <PlusOutlined /> {{ $t("home.form.addContext") }}
                </div>
              </a-form-item>
              <a-form-item :name="['annotation', index, 'answer']">
                <template #label>
                  <div class="flex-between">
                    <span>{{ $t("home.form.label.gt_answer") }}</span>
                    <FormTooltip
                      icon="QuestionCircleOutlined"
                      :title="$t('home.form.tip.gt_answer')"
                    />
                  </div>
                </template>
                <a-textarea
                  v-model:value="item.answer"
                  :disabled="item.isPass"
                  :placeholder="$t('home.form.placeholder.gt_answer')"
                  :auto-size="{ minRows: 1, maxRows: 2 }"
                />
              </a-form-item>
              <div class="icon-wrap" v-if="!item.isSubmit">
                <a-tooltip
                  placement="topRight"
                  arrow-point-at-center
                  :title="$t('home.form.delQuery')"
                  v-if="form.annotation?.length > 1"
                >
                  <MinusCircleOutlined @click="handleDelete(index)" />
                </a-tooltip>
              </div>
              <div class="flex-end" v-if="!item.isPass">
                <a-button
                  type="primary"
                  :icon="h(CheckCircleOutlined)"
                  @click="() => handleSingleSubmit(index)"
                >
                  {{ $t("common.save") }}
                </a-button>
              </div>
            </div>
          </transition>
        </div>
        <div class="operate-wrap" @click="handleAdd">
          <PlusOutlined />
          {{ $t("home.form.addQuery") }}
        </div>
      </a-form>
    </div>

    <template #footer>
      <div class="footer-wrap">
        <a-button :icon="h(ArrowLeftOutlined)" @click="handleClose">
          {{ $t("common.cancel") }}</a-button
        >
        <a-button
          v-if="allPass"
          type="primary"
          :icon="h(ArrowRightOutlined)"
          @click="handleSyncJson"
        >
          {{ $t("common.next") }}
        </a-button>
        <div v-else>
          <span class="text-wrap mr-8" v-if="totalSuggestions">
            <InfoCircleFilled
              :style="{ fontSize: '16px', color: 'var(--color-warning)' }"
            />
            {{ $t("home.checkTip") }}
          </span>
          <a-button
            type="primary"
            :icon="h(CheckCircleOutlined)"
            @click="handleBatchSubmit"
            :loading="submitLoading"
          >
            {{ $t("home.batchSub") }}
          </a-button>
        </div>
      </div>
    </template>
  </a-drawer>
</template>
<script lang="ts" setup name="CreateAnnotation">
import { FormInstance } from "ant-design-vue";
import { reactive, ref, h } from "vue";
import {
  getFileList,
  requestAnnotateSave,
  getAnnotateGroundTruth,
  requestAnnotationReset,
} from "@/api/ragPilot";
import {
  MinusCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ArrowLeftOutlined,
  UpOutlined,
  DownOutlined,
  ExclamationCircleFilled,
  ArrowRightOutlined,
  EditOutlined,
  InfoCircleFilled,
} from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";
import { FormType, QueryType, ContextItem, SuggestionItem } from "./type";
import { generateUniqueId } from "@/utils/common";
import { marked } from "marked";
import CustomRenderer from "@/utils/customRenderer";
import { formatPercentage } from "@/utils/common";

const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
  drawerType: {
    type: String,
    default: "create",
    required: true,
  },
});
marked.setOptions({
  pedantic: false,
  gfm: true,
  breaks: false,
  renderer: CustomRenderer,
});

const { t } = useI18n();
const emit = defineEmits(["close", "update"]);

const defaultQueryList = [
  {
    query: "",
    query_id: generateUniqueId(),
    answer: "",
    contexts: [
      {
        context_id: generateUniqueId(),
        filename: undefined,
        text: "",
        section: "",
        pages: "",
      },
    ],
  },
];
const inntAnnotationList = (data: QueryType[]) => {
  return data.map((query) => ({
    ...query,
    contexts: query.contexts.map((context) => ({
      ...context,
      pages: Array.isArray(context.pages)
        ? context.pages.join(", ")
        : String(context.pages || ""),
    })),
  }));
};

const { annotation = [] } = props.formData;
const drawerVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const fileList = ref<EmptyArrayType>([]);
const formRef = ref<FormInstance>();
const totalSuggestions = ref<number>(0);
const form = reactive<FormType>({
  annotation: annotation.length
    ? inntAnnotationList(annotation)
    : defaultQueryList,
});
const rules = reactive({
  query: [
    {
      required: true,
      message: t("home.form.valid.query"),
      trigger: "change",
    },
  ],
  fileName: [
    {
      required: true,
      message: t("home.form.valid.fileName"),
      trigger: "change",
    },
  ],
  contexts: [
    {
      required: true,
      type: "array",
      message: t("home.form.valid.gt_context"),
      trigger: "change",
    },
  ],
  text: [
    {
      required: true,
      message: t("home.form.valid.context"),
      trigger: "change",
    },
  ],
});
const isCreatee = computed(() => {
  return props.drawerType === "create";
});

const allPass = computed(() => {
  return form.annotation.every((item) => item.isPass);
});

const handlePagesChange = (context: ContextItem) => {
  const { pages } = context;
  context.pages = pages.replace(/[^0-9,]/g, "");
};
const handleSectionChange = (context: ContextItem) => {
  const { section } = context;
  context.section = section.replace(/[^0-9.]/g, "");
};

const handleAdd = () => {
  form.annotation.push({
    query: "",
    query_id: generateUniqueId(),
    answer: "",
    contexts: [
      {
        context_id: generateUniqueId(),
        filename: undefined,
        text: "",
        section: "",
        pages: "",
      },
    ],
  });
};
const handleDelete = (index: number) => {
  form.annotation.splice(index, 1);
};
const handleContextAdd = (contexts: ContextItem[]) => {
  contexts.push({
    context_id: generateUniqueId(),
    filename: undefined,
    text: "",
    section: "",
    pages: "",
  });
};
const handleContextDelete = (contexts: ContextItem[], index: number) => {
  contexts.splice(index, 1);
};
const handleFileVisible = async (visible: boolean) => {
  if (visible) {
    try {
      const data: any = await getFileList();
      fileList.value = [].concat(data?.documents);
    } catch (err) {
      console.error(err);
    }
  }
};
const toggleExpand = (row: QueryType) => {
  row.collapse = !row.collapse;
};

const handleSuggestionChange = (row: ContextItem, e: any) => {
  const nodeText = e.target.value;
  const suggestionMap = row?.suggestions?.find(
    (item: SuggestionItem) => item.best_match_context === nodeText
  ) as SuggestionItem;

  row.pages = suggestionMap?.node_page_label;
  row.isSelected = true;
};
const formatFormParam = (list: QueryType[]) => {
  return list.map((item) => {
    const { contexts } = item;
    return {
      ...item,
      contexts: contexts.map((context: ContextItem) => {
        const { pages } = context;
        return {
          ...context,
          pages: pages
            ? pages.split(",").map((page: string) => page.trim())
            : [],
        };
      }),
    };
  });
};
const handleSingleSubmit = async (index: number) => {
  try {
    if (!formRef.value) return;
    const currentItem = form.annotation[index];
    const singleVerify = [
      ["annotation", index, "query"],
      ["annotation", index, "contexts"],
    ];
    currentItem.contexts.forEach((_, contextIndex) => {
      singleVerify.push(
        ["annotation", index, "contexts", contextIndex, "filename"],
        ["annotation", index, "contexts", contextIndex, "text"]
      );
    });

    await formRef.value.validateFields(singleVerify);

    requestAnnotateSave(formatFormParam([currentItem]))
      .then((res: any) => {
        const { suggested_query_ids = [] } = res;
        form.annotation[index].isSubmit = true;
        form.annotation[index].contexts.forEach(
          (item) => (item.isSelected = false)
        );
        if (!suggested_query_ids.length) form.annotation[index].isPass = true;
        handleAnnotateSuggestion(suggested_query_ids);
      })
      .catch((error: any) => {
        console.error(error);
      });
  } catch (error) {
    console.error(error);
  }
};

const handleBatchSubmit = () => {
  formRef.value?.validate().then(() => {
    submitLoading.value = true;

    const batchQuery = form.annotation.filter((item) => !item.isPass);

    requestAnnotateSave(formatFormParam(batchQuery))
      .then((res: any) => {
        const { suggested_query_ids = [] } = res;

        form.annotation.forEach((query) => {
          query.isSubmit = true;
          query.contexts.forEach((item) => (item.isSelected = false));
          if (!suggested_query_ids.includes(query.query_id!)) {
            query.isPass = true;
          }
        });
        handleAnnotateSuggestion(suggested_query_ids);
      })
      .catch((error: any) => {
        console.error(error);
      })
      .finally(() => {
        submitLoading.value = false;
      });
  });
};
const handleAnnotateSuggestion = async (queryIds: number[]) => {
  try {
    const data = await getAnnotateGroundTruth();
    const suggestionQueries =
      data?.filter((item: QueryType) => queryIds.includes(item.query_id!)) ||
      [];
    totalSuggestions.value = getSuggestionsTotal(data);
    suggestionQueries.forEach(synchronizeFormData);
  } catch (error) {
    console.error(error);
  }
};
const getSuggestionsTotal = (data: QueryType[]) => {
  return data.reduce((total, query) => {
    return (
      total +
      query.contexts.filter((context) => {
        return context.suggestions && context.suggestions.length > 0;
      }).length
    );
  }, 0);
};
const synchronizeFormData = (suggestion: QueryType) => {
  const targetQuery = form.annotation.find(
    (item) => item.query_id === suggestion.query_id
  );

  if (!targetQuery) return;

  suggestion.contexts.forEach((context) => {
    const processedContext = {
      ...context,
      pages: Array.isArray(context.pages)
        ? context.pages.join(", ")
        : context.pages,
    };

    const targetContext = targetQuery.contexts.find(
      (ctx) => ctx.context_id === context.context_id
    );
    if (targetContext) {
      Object.assign(targetContext, processedContext);
    }
  });
};
const handleQueryEdit = (row: QueryType) => {
  row.isPass = false;
  row.isSubmit = false;
  row.collapse = false;
};
const handleSyncJson = () => {
  const storeData = form.annotation.map(
    ({ isSubmit, isPass, contexts, ...item }) => ({
      ...item,
      contexts: contexts.map((context) => {
        const { suggestions, pages, isSelected, ...restContext } = context;

        return {
          ...restContext,
          pages: pages
            ? pages.split(",").map((page: string) => page.trim())
            : [],
        };
      }),
    })
  );
  emit("update", { annotation: storeData });
  emit("close");
};
const handleClose = async () => {
  if (isCreatee.value) await requestAnnotationReset();

  emit("close");
};
</script>
<style scoped lang="less">
.enter-wrap {
  width: 75%;
  max-width: 960px;
  margin: 0 auto;
  .title-wrap {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 8px;
    color: var(--font-main-color);
  }
  .des-wrap {
    line-height: 24px;
    width: 100%;
    padding-bottom: 16px;
  }
  .form-wrap {
    .item-wrap {
      border: 1px solid var(--border-main-color);
      background-color: var(--bg-card-color);
      position: relative;
      margin-bottom: 16px;
      border-radius: 6px;
      .query-index {
        position: absolute;
        top: 0;
        left: 0;
        width: 22px;
        height: 22px;
        line-height: 22px;
        font-size: 12px;
        font-weight: 600;
        text-align: center;
        border-radius: 6px 0;
        color: var(--color-primary-tip);
        background-color: var(--border-primary);
      }
      .edit-icon {
        cursor: pointer;
        font-weight: 600;
        font-size: 16px;
        position: relative;
        color: var(--color-primary);
        &:hover {
          color: var(--color-primary-hover);
        }
      }
      .content-wrap {
        padding: 16px 48px 16px 16px;
        position: relative;
      }
      .flex-between {
        gap: 6px;
      }
      .gt-wrap {
        margin-bottom: 0;
        position: relative;
        :deep(.intel-form-item-control-input-content) {
          display: block;
        }
        .flex-item {
          flex: 1;
          :deep(.intel-form-item-control-input-content) {
            display: flex;
            align-items: center;
            gap: 6px;
          }
        }
      }
      .context-wrap {
        padding: 16px 16px 8px 16px;
        background-color: var(--bg-second-color);
        gap: 12px;
        margin-bottom: 12px;
        position: relative;
        .gt-index {
          position: absolute;
          top: 0;
          left: 0;
          width: 20px;
          height: 20px;
          line-height: 20px;
          font-size: 12px;
          font-weight: 600;
          text-align: center;
          border-radius: 6px 0;
          color: var(--color-success);
          background-color: var(--border-success);
        }
        .flex-left {
          gap: 12px;
        }
        :deep(.intel-form-item) {
          flex: 1;
        }
        .icon-wrap {
          justify-content: end;
        }
      }
      .add-wrap {
        .flex-end;
        gap: 6px;
        cursor: pointer;
        color: var(--color-primary);
        &:hover {
          color: var(--color-primary-hover);
        }
      }
      .flex-wrap {
        display: flex;
        gap: 6px;
        align-items: start;
      }
      .icon-wrap {
        position: absolute;
        top: 16px;
        right: 12px;
        width: 32px;
        cursor: pointer;
        display: inline-flex;
        justify-content: end;
        .anticon {
          font-size: 16px;
          &:hover {
            color: var(--color-primary);
          }
          &.anticon-delete {
            &:hover {
              color: var(--color-error) !important;
            }
          }
          &.anticon-minus-circle {
            &:hover {
              color: var(--color-error) !important;
            }
          }
        }
      }
      .slider-wrap {
        border-bottom: none !important;
      }
      .question-header {
        padding: 12px 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        cursor: pointer;
        transition: background-color 0.2s;
        border-bottom: 1px solid var(--border-main-color);
        .question-number {
          color: var(--color-primary-tip);
          background-color: var(--border-primary);
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
          margin-right: 8px;
          font-weight: 600;
        }

        .question-query {
          flex: 1;
          font-size: 16px;
          font-weight: 500;
          color: var(--font-main-color);
        }

        .arrow-icon {
          font-size: 12px;
          color: var(--font-tip-color);
        }
      }
    }
  }
}
.operate-wrap {
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  gap: 4px;
  border: 1px dashed var(--border-main-color);
  .vertical-center;
  &:hover {
    border: 1px dashed var(--color-primary-hover);
    color: var(--color-primary-hover);
  }
}
.footer-wrap {
  .flex-between;
}
.result-wrap {
  border: 1px solid var(--border-main-color);
  border-radius: 8px;
  padding: 2px 12px;
  background-color: var(--bg-card-color);
  margin-bottom: 8px;
  .intel-radio-group {
    width: 100%;
  }
  .option-item {
    display: flex;
    align-items: flex-start;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-main-color);

    &:last-child {
      border-bottom: none;
    }
    .intel-divider-horizontal {
      margin: 4px 0 8px 0;
    }

    .radio-wrap {
      width: 100%;
      text-align: start;
      .label-wrap {
        color: var(--font-info-color);
      }
    }
    .original-text {
      background-color: var(--color-infoBg);
      color: var(--font-info-color);
      word-break: break-word;
      padding: 4px;
      width: 100%;
      border-radius: 4px;
    }
  }

  :deep(.intel-radio-wrapper) {
    width: 100%;
  }

  :deep(.intel-radio + span) {
    flex: 1;
    display: inline-flex;
    padding-inline-end: 0;
  }
}
.warring-tip {
  border: 1px solid var(--border-warning);
  background-color: var(--color-warningBg);
  color: var(--color-second-warning);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  position: relative;
  top: -6px;
  .flex-left;
  .mb-8;
}
</style>
