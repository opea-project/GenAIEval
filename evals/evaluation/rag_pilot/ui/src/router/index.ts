import { createRouter, createWebHistory } from "vue-router";
import { notFoundRoute, routeList } from "./routes";

const router = createRouter({
  history: createWebHistory(),
  routes: [...notFoundRoute, ...routeList],
});

export default router;
