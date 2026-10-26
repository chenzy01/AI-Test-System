import React from "react";
import { Button } from "./button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./tooltip";
// eslint-disable  MC8yOmFIVnBZMlhsdktEbXRLcmxqWm82TTJjM2VBPT06ZDk0YzQ3Zjc=

interface TooltipIconButtonProps {
  icon: React.ReactNode;
  onClick: () => void;
  tooltip: string;
  disabled?: boolean;
}

export function TooltipIconButton({
  icon,
  onClick,
  tooltip,
  disabled,
}: TooltipIconButtonProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClick}
            disabled={disabled}
          >
            {icon}
          </Button>
        </TooltipTrigger>
        <TooltipContent>
          <p>{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
// eslint-disable  MS8yOmFIVnBZMlhsdktEbXRLcmxqWm82TTJjM2VBPT06ZDk0YzQ3Zjc=
