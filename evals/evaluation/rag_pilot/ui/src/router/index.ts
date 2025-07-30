import { createRouter, createWebHashHistory } from "vue-router";
import { notFoundRoute, routeList } from "./routes";

const router = createRouter({
  history: createWebHashHistory(),
  routes: [...notFoundRoute, ...routeList],
});

export default router;
