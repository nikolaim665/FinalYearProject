import { toast as sonnerToast } from "sonner";

interface ToastOptions {
  title?: string;
  description?: string;
  variant?: "default" | "destructive";
}

function toast(options: ToastOptions) {
  const { title, description, variant } = options;
  const message = title || "";
  const desc = description || "";

  if (variant === "destructive") {
    sonnerToast.error(message, { description: desc });
  } else {
    sonnerToast(message, { description: desc });
  }
}

function useToast() {
  return { toast };
}

export { useToast, toast };
