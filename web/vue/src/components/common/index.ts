/**
 * 通用组件总导出
 *
 * 提供跨模块共享的业务组件统一入口
 */

// 通用组件
export { Button } from "./general";
export { Card } from "./general";

// 表单组件
export { Input, Select, DateInput, TreeSelect, type TreeSelectProps } from "./form";

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
} from "./data-display";

// 反馈组件
export {
  Loading,
  Modal,
  MessageBox,
  SmartTooltip,
  PeopleSelectDialog,
  PeopleSelectView,
  usePeopleTree,
  type MessageBoxOptions,
  type MessageBoxType,
  type MessageBoxAction,
  type BeforeCloseCallback,
  type OrgTreeNode,
  type PeopleItem,
  type PeopleSelectEvent,
  type PeopleSelectOptions,
} from "./feedback";

// 导航组件
export { Pagination } from "./navigation";
