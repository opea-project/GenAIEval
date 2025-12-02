import { defineStore } from "pinia";

export const ragAppStore = defineStore("rag", {
  state: () => ({
    ragEndpoint: "",
  }),
  persist: {
    key: "rcrag",
    storage: localStorage,
  },
  actions: {
    setEndpointState(endpoint: string) {
      this.ragEndpoint = endpoint;
    },
  },
});
