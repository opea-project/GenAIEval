<template>
  <a-drawer
    v-model:open="drawerVisible"
    title="Prompt Edit"
    destroyOnClose
    width="600px"
    :keyboard="false"
    :maskClosable="false"
    @close="handleClose"
    class="update-drawer"
  >
    <a-form :model="form" :rules="rules" ref="formRef" autocomplete="off">
      <a-form-item label="Prompt" name="data">
        <template v-if="form.type === 'string'">
          <a-textarea v-model:value="form.data" :rows="5" :autoSize="false" />
        </template>
        <template v-else>
          <JsonEditorVue
            v-model="form.data"
            :showBtns="false"
            :expandedOnStart="true"
            theme="dark"
            @json-change="onJsonChange"
            @json-save="onJsonSave"
            class="json-wrap"
          />
        </template>
      </a-form-item>
    </a-form>
    <template #footer>
      <a-button style="margin-right: 8px" @click="handleClose">{{
        $t("common.cancel")
      }}</a-button>
      <a-button type="primary" :loading="submitLoading" @click="handleSubmit">{{
        $t("common.confirm")
      }}</a-button>
    </template>
  </a-drawer>
</template>
<script lang="ts" setup name="UpdateDrawer">
import { FormInstance } from "ant-design-vue";
import { reactive, ref } from "vue";
import { requesPromptUpdate } from "@/api/ragPilot";
import JsonEditorVue from "json-editor-vue";
import "jsoneditor/dist/jsoneditor.css";
import "jsoneditor/dist/jsoneditor.min.css";

const props = defineProps({
  drawerData: {
    type: Object,
    required: true,
    default: () => {},
  },
});
const emit = defineEmits(["close", "search"]);

const formRef = ref<FormInstance>();
const drawerVisible = ref<boolean>(true);
const submitLoading = ref<boolean>(false);
const { type = "", data = null } = props.drawerData;

const form = reactive<any>({
  type,
  data,
});
const rules = reactive({
  data: [{ required: true, trigger: "blur" }],
});
const onJsonChange = (value) => {};
const onJsonSave = (value) => {};

const handleClose = () => {
  emit("close");
};
const handleSubmit = () => {
  formRef.value?.validate().then(() => {
    submitLoading.value = true;
    requesPromptUpdate(form)
      .then(() => {
        emit("search");
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
</script>
<style scoped lang="less">
.update-drawer {
  .json-wrap {
    width: 100%;
    :deep(.jse-menu) {
      .jse-contextmenu,
      .jse-search,
      .jse-transform,
      .jse-sort,
      .jse-expand-all,
      .jse-collapse-all,
      .jse-separator {
        display: none !important;
      }
    }
  }
}
</style>
