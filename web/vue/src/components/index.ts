/**
 * 统一组件入口
 *
 * 导出策略：
 * 1. common 组件优先（同名组件覆盖 ui 版本）
 * 2. 高频 ui 组件重导出（common 没有的常用组件）
 * 3. 类型定义导出
 *
 * 使用方式：
 *   import { Button, Input, Dialog, Badge, Tree } from '@/components'
 *
 * 未包含的低频 ui 组件请从原始路径导入：
 *   import { Sidebar } from '@/components/ui/sidebar'
 */

// ── common 组件（优先导出，同名覆盖 ui） ──────────────────────────

// 通用组件
export { Button } from "./common/general/button";
export { Card } from "./common/general/card";

// 表单组件
export {
  Input,
  Select,
  DateInput,
  TreeSelect,
  type TreeSelectProps,
} from "./common/form";

// 数据展示组件
export {
  Table,
  DataTable,
  DataTablePagination,
  useDataTable,
  type DataTableState,
  Tree,
  TreeList,
  CheckboxTree,
  DescriptionList,
  type DescriptionItem,
} from "./common/data-display";

// 反馈组件
export {
  Loading,
  Modal,
  MessageBox,
  SmartTooltip,
  PeopleSelectDialog,
  PeopleSelectView,
  usePeopleTree,
  OrganizationSelect,
  OrganizationSelectDialog,
  OrganizationSelectView,
  useOrgTree,
  type MessageBoxOptions,
  type MessageBoxType,
  type MessageBoxAction,
  type BeforeCloseCallback,
  type OrgTreeNode,
  type PeopleItem,
  type PeopleSelectEvent,
  type PeopleSelectOptions,
  type OrgSelectNode,
  type OrgFlatNode,
  type OrgSelectOptions,
  type OrganizationItem,
  type OrganizationModelValue,
  type OrganizationConfirmEvent,
} from "./common/feedback";

// 导航组件
export { Pagination } from "./common/navigation";

// ── 高频 ui 组件（common 没有，重导出） ──────────────────────────

// 基础控件
export { Badge } from "./ui/badge";
export { Skeleton } from "./ui/skeleton";
export { Label } from "./ui/label";
export { Checkbox } from "./ui/checkbox";
export { Switch } from "./ui/switch";
export { Textarea } from "./ui/textarea";

// Dialog 复合组件
export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogScrollContent,
  DialogTitle,
  DialogTrigger,
} from "./ui/dialog";

// Tabs 复合组件
export {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "./ui/tabs";

// Form 复合组件
export {
  FormControl,
  FormDescription,
  FormItem,
  FormLabel,
  FormMessage,
  Form,
  FormField,
  FormFieldArray,
} from "./ui/form";
