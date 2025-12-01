import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';

export interface UploadResponse {
  job_id: string;
  message: string;
  filename: string;
}

export interface BookMetadata {
  title: string;
  author: string;
  language: string;
  total_chapters: number;
  total_words: number;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'extracting' | 'splitting' | 'analyzing' | 'generating' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  error_message?: string;
  metadata?: BookMetadata;
  output_ready: boolean;
}

export interface DownloadInfo {
  md_available: boolean;
  pdf_available: boolean;
  md_filename?: string;
  pdf_filename?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;

  /**
   * Upload a book file for analysis
   */
  uploadBook(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    // Para upload de arquivo, precisa usar multipart/form-data
    return this.http.post<UploadResponse>(`${this.baseUrl}/api/upload`, formData, {
      reportProgress: true
    });
  }

  /**
   * Get job status
   */
  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.baseUrl}/api/status/${jobId}`);
  }

  /**
   * Get download info
   */
  getDownloadInfo(jobId: string): Observable<DownloadInfo> {
    return this.http.get<DownloadInfo>(`${this.baseUrl}/api/download/${jobId}/info`);
  }

  /**
   * Get download URL for Markdown
   */
  getMarkdownDownloadUrl(jobId: string): string {
    return `${this.baseUrl}/api/download/${jobId}/md`;
  }

  /**
   * Get download URL for PDF
   */
  getPdfDownloadUrl(jobId: string): string {
    return `${this.baseUrl}/api/download/${jobId}/pdf`;
  }

  /**
   * Delete a job
   */
  deleteJob(jobId: string): Observable<{ message: string }> {
    return this.http.delete<{ message: string }>(`${this.baseUrl}/api/jobs/${jobId}`);
  }
}

