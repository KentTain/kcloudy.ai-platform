export interface Dataset {
  id: string;
  name: string;
  description?: string;
  createdAt?: string;
  updatedAt?: string;
}

export interface CreateDatasetRequest {
  name: string;
  description?: string;
}
