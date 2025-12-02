import { defineStore } from "pinia";

export const pipelineAppStore = defineStore("pipeline", {
  state: () => ({
    basePipeline: null,
  }),
  persist: {
    key: "pipelineInfo",
    storage: localStorage,
  },
  actions: {
    setPipeline(id: any) {
      this.basePipeline = id;
    },
  },
});
