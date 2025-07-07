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
      <div class="title-wrap">{{ $t("home.create") }}</div>
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
          v-for="(item, index) in form.groundtruths"
          :key="index"
        >
          <a-form-item
            :label="`${$t('home.form.label.query')} ${index + 1}`"
            :name="['groundtruths', index, 'query']"
            :rules="rules.query"
          >
            <a-textarea
              v-model:value="item.query"
              :placeholder="$t('home.form.placeholder.query')"
              :auto-size="{ minRows: 1, maxRows: 2 }"
            />
            <FormTooltip :title="$t('home.form.tip.query')" />
          </a-form-item>
          <a-form-item
            :label="$t('home.form.label.gt_context')"
            :name="['groundtruths', index, 'contexts']"
            :rules="rules.contexts"
            class="gt-wrap"
          >
            <div
              v-for="(context, k) in item.contexts"
              :key="k"
              class="item-wrap context-wrap flex-left"
            >
              <a-form-item
                :label="$t('home.form.label.fileName')"
                :name="['groundtruths', index, 'contexts', k, 'filename']"
                :rules="rules.fileName"
                class="flex-item"
              >
                <a-input
                  v-model:value="context.filename"
                  :placeholder="$t('home.form.placeholder.fileName')"
                />
                <FormTooltip :title="$t('home.form.tip.fileName')" />
              </a-form-item>

              <a-form-item
                :label="$t('home.form.label.context')"
                :name="['groundtruths', index, 'contexts', k, 'text']"
                :rules="rules.text"
                class="flex-item"
              >
                <a-textarea
                  v-model:value="context.text"
                  :placeholder="$t('home.form.placeholder.context')"
                  :auto-size="{ minRows: 1, maxRows: 5 }"
                />
                <FormTooltip :title="$t('home.form.tip.context')" />
              </a-form-item>

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
            </div>
            <div class="add-wrap" @click="handleContextAdd(item.contexts)">
              <PlusOutlined /> {{ $t("home.form.addContext") }}
            </div>
          </a-form-item>
          <a-form-item
            :label="$t('home.form.label.gt_answer')"
            :name="['groundtruths', index, 'answer']"
          >
            <a-textarea
              v-model:value="item.answer"
              :placeholder="$t('home.form.placeholder.gt_answer')"
              :auto-size="{ minRows: 1, maxRows: 2 }"
            /><FormTooltip :title="$t('home.form.tip.gt_answer')" />
          </a-form-item>
          <div class="icon-wrap">
            <a-tooltip
              placement="topRight"
              arrow-point-at-center
              :title="$t('home.form.addQuery')"
            >
              <PlusCircleOutlined @click="handleAdd" />
            </a-tooltip>
            <a-tooltip
              placement="topRight"
              arrow-point-at-center
              :title="$t('home.form.delQuery')"
              v-if="form.groundtruths?.length > 1"
            >
              <MinusCircleOutlined @click="handleDelete(index)" />
            </a-tooltip>
          </div>
        </div>
      </a-form>
    </div>

    <template #footer>
      <div class="footer-wrap">
        <a-button style="margin-right: 8px" @click="handleClose">
          <ArrowLeftOutlined />
          {{ $t("common.cancel") }}</a-button
        >
        <a-button type="primary" :loading="submitLoading" @click="handleSubmit"
          >{{ $t("common.next") }} <ArrowRightOutlined
        /></a-button>
      </div>
    </template>
  </a-drawer>
</template>
<script lang="ts" setup name="UpdateDrawer">
import { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { requestSubmitQueryJson } from "@/api/ragPilot";
import {
  PlusCircleOutlined,
  MinusCircleOutlined,
  PlusOutlined,
  DeleteOutlined,
  ArrowRightOutlined,
  ArrowLeftOutlined,
} from "@ant-design/icons-vue";
import { useI18n } from "vue-i18n";

const props = defineProps({
  formData: {
    type: Object,
    default: () => {},
  },
});
const { t } = useI18n();
const emit = defineEmits(["close", "update"]);

interface FormType {
  groundtruths: QueryType[];
}
interface ContextItem {
  filename: "";
  text: "";
}
interface QueryType {
  query: string;
  answer: string;
  contexts: ContextItem[];
}

const defaultQueryList = [
  {
    query: "",
    answer: "",
    contexts: [
      {
        filename: "",
        text: "",
      },
    ],
  },
];
const { groundtruths = [] } = props.formData;
const drawerVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const formRef = ref<FormInstance>();
const form = reactive<FormType>({
  groundtruths: groundtruths.length ? groundtruths : defaultQueryList,
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

const handleAdd = () => {
  form.groundtruths.push({
    query: "",
    answer: "",
    contexts: [
      {
        filename: "",
        text: "",
      },
    ],
  });
};
const handleDelete = (index: number) => {
  form.groundtruths.splice(index, 1);
};
const handleContextAdd = (contexts: ContextItem[]) => {
  contexts.push({
    filename: "",
    text: "",
  });
};
const handleContextDelete = (contexts: ContextItem[], index: number) => {
  contexts.splice(index, 1);
};
const formatFormParam = () => {
  return form.groundtruths.map((item, index) => {
    return {
      query_id: index + 1,
      ...item,
    };
  });
};
const handleSubmit = () => {
  formRef.value?.validate().then(() => {
    submitLoading.value = true;

    requestSubmitQueryJson(formatFormParam())
      .then(() => {
        emit("update", form);
        handleClose();
      })
      .catch((error: any) => {
        console.error(error);
      })
      .finally(() => {
        submitLoading.value = false;
      });
  });
};
const handleClose = () => {
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
    margin-bottom: 16px;
    color: var(--font-main-color);
  }
  .form-wrap {
    .item-wrap {
      padding: 16px 32px 0 16px;
      border: 1px solid var(--border-main-color);
      background-color: var(--bg-card-color);
      position: relative;
      margin-bottom: 16px;
      border-radius: 6px;
      .gt-wrap {
        margin-bottom: 0;
        :deep(.intel-form-item-control-input-content) {
          display: block;
          padding-right: 22px;
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
        background-color: var(--bg-second-color);
        gap: 12px;
        padding-right: 16px;
        padding-bottom: 8px;
        margin-bottom: 12px;
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
        cursor: pointer;
        display: inline-flex;
        gap: 8px;
        width: 42px;
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
    }
  }
}
.footer-wrap {
  .flex-between;
}
</style>
