import { createRouter, createWebHashHistory } from "vue-router";

const routes = [
  {
    path: "/",
    name: "Dashboard",
    component: () => import("../views/Dashboard.vue"),
  },
  {
    path: "/keywords",
    name: "Keywords",
    component: () => import("../views/Keywords.vue"),
  },
  {
    path: "/journals",
    name: "Journals",
    component: () => import("../views/Journals.vue"),
  },
  {
    path: "/settings",
    name: "Settings",
    component: () => import("../views/Settings.vue"),
  },
  {
    path: "/local-papers",
    name: "LocalPapers",
    component: () => import("../views/LocalPapers.vue"),
  },
  {
    path: "/history",
    name: "History",
    component: () => import("../views/History.vue"),
  },
  {
    path: "/logs",
    name: "Logs",
    component: () => import("../views/Logs.vue"),
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

export default router;
