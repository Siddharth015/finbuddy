/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_DEV_INIT_DATA: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface TelegramHapticFeedback {
  impactOccurred: (style: string) => void;
  notificationOccurred: (type: string) => void;
  selectionChanged?: () => void;
}

interface TelegramMainButton {
  text: string;
  isVisible: boolean;
  isActive: boolean;
  setText: (text: string) => void;
  show: () => void;
  hide: () => void;
  enable: () => void;
  disable: () => void;
  showProgress: (leaveActive?: boolean) => void;
  hideProgress: () => void;
  onClick: (cb: () => void) => void;
  offClick: (cb: () => void) => void;
  setParams: (params: Record<string, unknown>) => void;
}

interface TelegramBackButton {
  isVisible: boolean;
  show: () => void;
  hide: () => void;
  onClick: (cb: () => void) => void;
  offClick: (cb: () => void) => void;
}

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      username?: string;
    };
  };
  colorScheme: "light" | "dark";
  themeParams: Record<string, string>;
  ready: () => void;
  expand: () => void;
  close: () => void;
  HapticFeedback?: TelegramHapticFeedback;
  MainButton?: TelegramMainButton;
  BackButton?: TelegramBackButton;
  showAlert?: (message: string) => void;
  showConfirm?: (message: string, cb: (ok: boolean) => void) => void;
  setHeaderColor?: (color: string) => void;
  setBackgroundColor?: (color: string) => void;
  onEvent?: (event: string, cb: () => void) => void;
  offEvent?: (event: string, cb: () => void) => void;
}

interface Window {
  Telegram?: {
    WebApp: TelegramWebApp;
  };
}
