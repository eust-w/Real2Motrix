export const locales = ["zh", "en"] as const;
export type Locale = (typeof locales)[number];

export const defaultLocale: Locale = "zh";

export const localeLabels: Record<Locale, string> = {
  zh: "中文",
  en: "English"
};

const messages = {
  zh: {
    "actions.create": "创建",
    "actions.package": "下载包",
    "actions.preview": "预览",
    "actions.refresh": "刷新",
    "actions.startPipeline": "启动流水线",
    "actions.validate": "验证",
    "assets.subtitle": "输出",
    "assets.collisionMesh": "碰撞网格",
    "assets.empty": "生成的 Motrix 资产会显示在这里。",
    "assets.motrixPackage": "Motrix 包",
    "assets.objectCollisionMesh": "物体碰撞网格",
    "assets.objectVisualMesh": "物体视觉网格",
    "assets.sceneCollisionMesh": "场景碰撞网格",
    "assets.sceneVisualMesh": "场景视觉网格",
    "assets.title": "资产",
    "assets.visualMesh": "视觉网格",
    "brand.subtitle": "本地流水线",
    "dependencies.missing": "缺失",
    "dependencies.ready": "就绪",
    "dependencies.title": "依赖",
    "form.description": "描述",
    "form.projectName": "项目名称",
    "input.dropZone": "选择真实采集、视频、网格、点云或导出文件",
    "input.sourceType": "源类型",
    "input.subtitle": "输入",
    "input.title": "上传并运行",
    "language.en": "English",
    "language.label": "语言",
    "language.switchTo": "切换到 {language}",
    "language.zh": "中文",
    "logs.empty": "Worker 启动作业后会显示日志。",
    "logs.subtitle": "Worker",
    "logs.title": "日志",
    "newProject.title": "新项目",
    "preview.collisionAsset": "碰撞资产",
    "preview.completeScene": "完整场景",
    "preview.loadingAsset": "正在加载 3D 资产。",
    "preview.loadingScene": "正在加载 Motrix 场景。",
    "preview.motrixScene": "Motrix 场景",
    "preview.objects": "物体：{count}",
    "preview.subtitle": "3D 预览",
    "preview.title": "Motrix 场景 / 3D 资产",
    "preview.unavailable": "生成场景资产后才能预览。",
    "preview.visualAsset": "视觉资产",
    "projects.title": "项目",
    "source.images": "图片",
    "source.ios_capture": "iOS 采集",
    "source.mesh": "网格",
    "source.nerfstudio": "Nerfstudio",
    "source.pointcloud": "点云",
    "source.polycam": "Polycam",
    "source.scaniverse": "Scaniverse",
    "source.video": "视频",
    "stats.bbox": "包围盒：{value}",
    "stats.collisionFaces": "碰撞面数：{value}",
    "stats.visualFaces": "视觉面数：{value}",
    "status.completed": "已完成",
    "status.created": "已创建",
    "status.failed": "失败",
    "status.queued": "排队中",
    "status.running": "运行中",
    "task.empty": "当前项目还没有启动作业。",
    "task.error": "错误",
    "task.source": "源",
    "task.step": "步骤",
    "task.subtitle": "任务",
    "task.title": "作业进度",
    "validation.empty": "生成包后运行验证。",
    "validation.invalid": "无效",
    "validation.noIssues": "没有验证问题。",
    "validation.subtitle": "包",
    "validation.title": "验证",
    "validation.valid": "有效",
    "workspace.noProject": "未选择项目",
    "workspace.subtitle": "工作区"
  },
  en: {
    "actions.create": "Create",
    "actions.package": "Package",
    "actions.preview": "Preview",
    "actions.refresh": "Refresh",
    "actions.startPipeline": "Start pipeline",
    "actions.validate": "Validate",
    "assets.subtitle": "Output",
    "assets.collisionMesh": "collision_mesh",
    "assets.empty": "Generated Motrix assets will appear here.",
    "assets.motrixPackage": "motrix_package",
    "assets.objectCollisionMesh": "object collision_mesh",
    "assets.objectVisualMesh": "object visual_mesh",
    "assets.sceneCollisionMesh": "scene_collision_mesh",
    "assets.sceneVisualMesh": "scene_visual_mesh",
    "assets.title": "Assets",
    "assets.visualMesh": "visual_mesh",
    "brand.subtitle": "Local pipeline",
    "dependencies.missing": "missing",
    "dependencies.ready": "ready",
    "dependencies.title": "Dependencies",
    "form.description": "Description",
    "form.projectName": "Project name",
    "input.dropZone": "Select real capture, video, mesh, point cloud, or export files",
    "input.sourceType": "Source type",
    "input.subtitle": "Input",
    "input.title": "Upload and run",
    "language.en": "English",
    "language.label": "Language",
    "language.switchTo": "Switch to {language}",
    "language.zh": "中文",
    "logs.empty": "Logs appear after the worker starts a job.",
    "logs.subtitle": "Worker",
    "logs.title": "Logs",
    "newProject.title": "New project",
    "preview.collisionAsset": "Collision Asset",
    "preview.completeScene": "complete_scene",
    "preview.loadingAsset": "Loading 3D asset.",
    "preview.loadingScene": "Loading Motrix scene.",
    "preview.motrixScene": "Motrix Scene",
    "preview.objects": "objects: {count}",
    "preview.subtitle": "3D preview",
    "preview.title": "Motrix scene / 3D assets",
    "preview.unavailable": "Preview is unavailable until generated scene assets exist.",
    "preview.visualAsset": "Visual Asset",
    "projects.title": "Projects",
    "source.images": "images",
    "source.ios_capture": "ios_capture",
    "source.mesh": "mesh",
    "source.nerfstudio": "nerfstudio",
    "source.pointcloud": "pointcloud",
    "source.polycam": "polycam",
    "source.scaniverse": "scaniverse",
    "source.video": "video",
    "stats.bbox": "bbox: {value}",
    "stats.collisionFaces": "collision faces: {value}",
    "stats.visualFaces": "visual faces: {value}",
    "status.completed": "completed",
    "status.created": "created",
    "status.failed": "failed",
    "status.queued": "queued",
    "status.running": "running",
    "task.empty": "No job has been started for this project.",
    "task.error": "Error",
    "task.source": "Source",
    "task.step": "Step",
    "task.subtitle": "Task",
    "task.title": "Job progress",
    "validation.empty": "Run validation after a package has been generated.",
    "validation.invalid": "invalid",
    "validation.noIssues": "No validation issues.",
    "validation.subtitle": "Package",
    "validation.title": "Validation",
    "validation.valid": "valid",
    "workspace.noProject": "No project selected",
    "workspace.subtitle": "Workspace"
  }
} satisfies Record<Locale, Record<string, string>>;

export type TranslationKey = keyof (typeof messages)["zh"];
export type Translator = (key: TranslationKey, values?: Record<string, string | number>) => string;

export function isLocale(value: unknown): value is Locale {
  return typeof value === "string" && (locales as readonly string[]).includes(value);
}

export function nextLocale(locale: Locale): Locale {
  return locale === "zh" ? "en" : "zh";
}

export function translate(locale: Locale, key: TranslationKey, values: Record<string, string | number> = {}): string {
  let message = messages[locale][key] ?? messages[defaultLocale][key] ?? key;
  for (const [name, value] of Object.entries(values)) {
    message = message.split(`{${name}}`).join(String(value));
  }
  return message;
}

export function createTranslator(locale: Locale): Translator {
  return (key: TranslationKey, values?: Record<string, string | number>) => translate(locale, key, values);
}

export function readStoredLocale(storage: Pick<Storage, "getItem"> | undefined = globalThis.localStorage): Locale {
  try {
    const stored = storage?.getItem("real2motrix.locale");
    return isLocale(stored) ? stored : defaultLocale;
  } catch {
    return defaultLocale;
  }
}
