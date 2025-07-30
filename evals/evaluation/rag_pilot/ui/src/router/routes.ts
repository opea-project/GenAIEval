import Layout from "@/layout/Main.vue";

export const routeList = [
  {
    path: "/",
    name: "Main",
    component: Layout,
    redirect: "/home",
    children: [
      {
        path: "/home",
        name: "Home",
        component: () => import("@/views/home/index.vue"),
        meta: { title: "Home" },
      },
      {
        path: "/tuner",
        name: "Tuner",
        component: () => import("@/views/tuner/index.vue"),
        redirect: "/tuner/rating",
        children: [
          {
            path: "/tuner/rating",
            name: "Rating",
            component: () => import("@/views/tuner/components/Rating.vue"),
          },
          {
            path: "/tuner/retrieve",
            name: "Retrieve",
            component: () => import("@/views/tuner/components/Retrieve.vue"),
          },
          {
            path: "/tuner/postprocess",
            name: "Postprocess",
            component: () => import("@/views/tuner/components/Postprocess.vue"),
          },
          {
            path: "/tuner/generation",
            name: "Generation",
            component: () => import("@/views/tuner/components/Generation.vue"),
          },
          {
            path: "/tuner/results",
            name: "Results",
            component: () => import("@/views/tuner/components/Results.vue"),
          },
        ],
      },
    ],
  },
];

export const notFoundRoute = [
  {
    path: "/:path(.*)*",
    name: "notFound",
    component: () => import("@/views/error/404.vue"),
    meta: {
      title: "404",
    },
  },
];
