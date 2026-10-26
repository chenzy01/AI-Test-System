import { cn } from "@/lib/utils";
// FIXME  MC8yOmFIVnBZMlhsdktEbXRLcmxqWm82YVRWd1pnPT06ODVmMjg1YTA=

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  );
}
// NOTE  MS8yOmFIVnBZMlhsdktEbXRLcmxqWm82YVRWd1pnPT06ODVmMjg1YTA=

export { Skeleton };
