import type { Artifact } from "@/types/domain";

/**
 * Renders an artifact's inline preview content. The mock backend ships text /
 * markdown / code / json previews; richer types fall back to a description.
 */
export function ArtifactViewer({ artifact }: { artifact: Artifact }) {
  const { type, content } = artifact;

  if (!content) {
    return (
      <div className="rounded-md border border-dashed border-border p-8 text-center text-sm text-muted-foreground">
        No inline preview available for this {type} artifact.
      </div>
    );
  }

  if (type === "SourceCode" || type === "JSON") {
    return (
      <pre className="max-h-full overflow-auto rounded-md bg-muted p-3 text-xs leading-relaxed scrollbar-thin">
        <code>{content}</code>
      </pre>
    );
  }

  // Markdown / Document / Research / Specification etc: render as preformatted text.
  return (
    <div className="whitespace-pre-wrap rounded-md border border-border bg-card p-4 text-sm leading-relaxed">
      {content}
    </div>
  );
}
