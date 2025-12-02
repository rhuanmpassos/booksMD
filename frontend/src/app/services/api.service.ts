import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject, from } from 'rxjs';
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
  md_ready?: boolean;
  pdf_ready?: boolean;
}

export interface ExtractResponse {
  success: boolean;
  totalChapters: number;
  bookMetadata: BookMetadata;
}

export interface AnalyzeResponse {
  success: boolean;
  chapterIndex: number;
  analyzedChapters: number;
  totalChapters: number;
  completed: boolean;
}

export interface GenerateResponse {
  success: boolean;
  outputUrl: string;
  filename: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private baseUrl = environment.apiUrl;
  
  // Subject para cancelar processamento
  private cancelProcessing$ = new Subject<void>();

  /**
   * Upload a book file using Vercel Blob client-side upload
   */
  uploadBook(file: File): Observable<UploadResponse> {
    return from(this.uploadToBlob(file));
  }

  private async uploadToBlob(file: File): Promise<UploadResponse> {
    // Importa dinamicamente o cliente do Vercel Blob
    const { upload } = await import('@vercel/blob/client');
    
    const blob = await upload(file.name, file, {
      access: 'public',
      handleUploadUrl: `${this.baseUrl}/api/upload`,
    });

    // Extrai job_id do pathname (formato: books/{jobId}/filename)
    const pathParts = blob.pathname.split('/');
    const jobId = pathParts.length >= 2 ? pathParts[1] : '';
    
    if (!jobId) {
      throw new Error('Failed to get job ID from upload response');
    }

    return {
      job_id: jobId,
      message: 'Upload successful',
      filename: file.name,
    };
  }

  /**
   * Get job status
   */
  getJobStatus(jobId: string): Observable<JobStatus> {
    return this.http.get<JobStatus>(`${this.baseUrl}/api/status/${jobId}`);
  }

  /**
   * Extract text and split into chapters
   */
  extractChapters(jobId: string): Observable<ExtractResponse> {
    return this.http.post<ExtractResponse>(`${this.baseUrl}/api/extract`, { jobId });
  }

  /**
   * Analyze a single chapter
   */
  analyzeChapter(jobId: string, chapterIndex: number): Observable<AnalyzeResponse> {
    return this.http.post<AnalyzeResponse>(`${this.baseUrl}/api/analyze`, { 
      jobId, 
      chapterIndex 
    });
  }

  /**
   * Generate final Markdown document
   */
  generateDocument(jobId: string): Observable<GenerateResponse> {
    return this.http.post<GenerateResponse>(`${this.baseUrl}/api/generate`, { jobId });
  }

  /**
   * Process entire book (orchestrates all steps)
   * This is called from the frontend to process chapter by chapter
   */
  processBook(jobId: string, onProgress: (status: JobStatus) => void): Observable<JobStatus> {
    return new Observable(observer => {
      this.runProcessing(jobId, onProgress, observer);
    });
  }

  private async runProcessing(
    jobId: string, 
    onProgress: (status: JobStatus) => void,
    observer: any
  ) {
    try {
      // 1. Extract chapters
      onProgress({
        job_id: jobId,
        status: 'extracting',
        progress: 5,
        current_step: 'Extraindo texto do arquivo...',
        output_ready: false
      });

      const extractResult = await this.extractChapters(jobId).toPromise();
      
      if (!extractResult?.success) {
        throw new Error('Failed to extract chapters');
      }

      const totalChapters = extractResult.totalChapters;

      // 2. Analyze each chapter
      for (let i = 0; i < totalChapters; i++) {
        onProgress({
          job_id: jobId,
          status: 'analyzing',
          progress: 20 + (i / totalChapters) * 60,
          current_step: `Analisando capítulo ${i + 1} de ${totalChapters}...`,
          metadata: extractResult.bookMetadata,
          output_ready: false
        });

        const analyzeResult = await this.analyzeChapter(jobId, i).toPromise();
        
        if (!analyzeResult?.success) {
          console.warn(`Chapter ${i} analysis failed, continuing...`);
        }

        // Small delay between chapters to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
      }

      // 3. Generate final document
      onProgress({
        job_id: jobId,
        status: 'generating',
        progress: 85,
        current_step: 'Gerando documento final...',
        metadata: extractResult.bookMetadata,
        output_ready: false
      });

      const generateResult = await this.generateDocument(jobId).toPromise();

      if (!generateResult?.success) {
        throw new Error('Failed to generate document');
      }

      // 4. Complete
      const finalStatus: JobStatus = {
        job_id: jobId,
        status: 'completed',
        progress: 100,
        current_step: 'Concluído!',
        metadata: extractResult.bookMetadata,
        output_ready: true,
        md_ready: true
      };

      onProgress(finalStatus);
      observer.next(finalStatus);
      observer.complete();

    } catch (error: any) {
      const errorStatus: JobStatus = {
        job_id: jobId,
        status: 'failed',
        progress: 0,
        current_step: 'Erro no processamento',
        error_message: error.message,
        output_ready: false
      };
      
      onProgress(errorStatus);
      observer.error(error);
    }
  }

  /**
   * Cancel ongoing processing
   */
  cancelProcessing(): void {
    this.cancelProcessing$.next();
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
   * Delete a job (files are auto-deleted on download)
   */
  deleteJob(jobId: string): Observable<{ message: string }> {
    // No Node.js version, files are auto-deleted on download
    return of({ message: 'Job will be deleted on download' });
  }
}
