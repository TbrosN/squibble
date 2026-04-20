import type { ButtonHTMLAttributes } from "react";
import { Button } from "./Button";

type CancelButtonProps = Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "children"
> & {
  label?: string;
};

export function CancelButton({
  label = "Cancel",
  ...rest
}: CancelButtonProps) {
  return (
    <Button variant="danger" size="md" {...rest}>
      {label}
    </Button>
  );
}
