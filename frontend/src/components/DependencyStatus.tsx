import { CheckCircle2, CircleAlert } from "lucide-react";
import type { Translator } from "../lib/i18n";
import type { Health } from "../lib/types";

const critical = ["ffmpeg", "colmap", "InterfaceCOLMAP", "DensifyPointCloud", "ReconstructMesh", "blender", "xcodebuild"];

export function DependencyStatus({ health, t }: { health: Health | null; t: Translator }) {
  return (
    <div className="dependency-box">
      <div className="section-title">{t("dependencies.title")}</div>
      {critical.map((name) => {
        const item = health?.dependencies[name];
        const ok = Boolean(item?.available);
        return (
          <div className={ok ? "dependency-row ready" : "dependency-row missing"} key={name}>
            {ok ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}
            <span>{name}</span>
            <small>{ok ? t("dependencies.ready") : t("dependencies.missing")}</small>
          </div>
        );
      })}
    </div>
  );
}
