import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="container mx-auto px-6 py-12">
      <!-- Hero Section -->
      <section class="text-center mb-16 animate-fade-in">
        <h1 class="text-5xl md:text-7xl font-display font-bold mb-6">
          <span class="text-ink-100">Transforme livros em</span>
          <br>
          <span class="text-gradient">conhecimento estruturado</span>
        </h1>
        <p class="text-xl text-ink-400 max-w-2xl mx-auto mb-8 font-body">
          Análise profunda de livros com inteligência artificial. 
          Upload seu PDF, EPUB ou TXT e receba uma análise detalhada em Markdown ou PDF.
        </p>
        
        <!-- Features -->
        <div class="flex flex-wrap justify-center gap-6 text-sm text-ink-400">
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-gold-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span>Análise por capítulos</span>
          </div>
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-gold-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"/>
            </svg>
            <span>Tradução automática</span>
          </div>
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-gold-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
            </svg>
            <span>Glossário técnico</span>
          </div>
          <div class="flex items-center gap-2">
            <svg class="w-5 h-5 text-gold-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            <span>Export MD & PDF</span>
          </div>
        </div>
      </section>
      
      <!-- Upload Section -->
      <section class="max-w-3xl mx-auto animate-slide-up" style="animation-delay: 0.2s">
        <div class="card p-8">
          <!-- Upload Zone -->
          <div 
            class="upload-zone"
            [class.dragover]="isDragOver"
            (dragover)="onDragOver($event)"
            (dragleave)="onDragLeave($event)"
            (drop)="onDrop($event)"
            (click)="fileInput.click()">
            
            <input 
              #fileInput
              type="file" 
              class="hidden"
              accept=".pdf,.epub,.txt"
              (change)="onFileSelected($event)">
            
            <div class="text-center">
              <!-- Icon -->
              <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-ink-800/50 mb-6">
                <svg class="w-10 h-10 text-gold-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" 
                        d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"/>
                </svg>
              </div>
              
              <h3 class="text-xl font-semibold text-ink-100 mb-2">
                Arraste seu livro aqui
              </h3>
              <p class="text-ink-400 mb-4">
                ou clique para selecionar
              </p>
              
              <!-- Formats -->
              <div class="flex justify-center gap-3">
                <span class="px-3 py-1 rounded-full bg-ink-800/50 text-ink-300 text-sm">.pdf</span>
                <span class="px-3 py-1 rounded-full bg-ink-800/50 text-ink-300 text-sm">.epub</span>
                <span class="px-3 py-1 rounded-full bg-ink-800/50 text-ink-300 text-sm">.txt</span>
              </div>
            </div>
          </div>
          
          <!-- Selected File -->
          @if (selectedFile) {
            <div class="mt-6 p-4 rounded-xl bg-ink-800/30 border border-ink-700/30">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 rounded-xl bg-gold-500/10 flex items-center justify-center">
                    <svg class="w-6 h-6 text-gold-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                  </div>
                  <div>
                    <p class="font-medium text-ink-100">{{ selectedFile.name }}</p>
                    <p class="text-sm text-ink-400">{{ formatFileSize(selectedFile.size) }}</p>
                  </div>
                </div>
                <button 
                  (click)="clearFile($event)"
                  class="p-2 rounded-lg hover:bg-ink-700/50 text-ink-400 hover:text-ink-200 transition-colors">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </button>
              </div>
            </div>
          }
          
          <!-- Upload Button -->
          <div class="mt-8 flex justify-center">
            <button 
              class="btn-primary text-lg px-10 py-4"
              [disabled]="!selectedFile || isUploading"
              (click)="uploadFile()">
              @if (isUploading) {
                <svg class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                  <path class="opacity-75" fill="currentColor" 
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
                </svg>
                <span>Enviando...</span>
              } @else {
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                <span>Iniciar Análise</span>
              }
            </button>
          </div>
          
          <!-- Error -->
          @if (error) {
            <div class="mt-6 p-4 rounded-xl bg-wine-500/10 border border-wine-500/30">
              <p class="text-wine-400 text-center">{{ error }}</p>
            </div>
          }
        </div>
      </section>
      
      <!-- How it Works -->
      <section class="mt-24 max-w-5xl mx-auto">
        <h2 class="text-3xl font-display font-bold text-center text-ink-100 mb-12">
          Como Funciona
        </h2>
        
        <div class="grid md:grid-cols-4 gap-8">
          @for (step of steps; track step.number; let i = $index) {
            <div class="relative text-center animate-slide-up" [style.animation-delay.ms]="i * 100">
              <!-- Connector -->
              @if (i < steps.length - 1) {
                <div class="hidden md:block absolute top-8 left-[60%] w-[80%] h-px bg-gradient-to-r from-gold-500/50 to-transparent"></div>
              }
              
              <!-- Number -->
              <div class="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-ink-800/50 border border-ink-700/30 mb-4">
                <span class="text-2xl font-display font-bold text-gradient">{{ step.number }}</span>
              </div>
              
              <h3 class="font-semibold text-ink-100 mb-2">{{ step.title }}</h3>
              <p class="text-sm text-ink-400">{{ step.description }}</p>
            </div>
          }
        </div>
      </section>
    </div>
  `
})
export class HomeComponent {
  private router = inject(Router);
  private api = inject(ApiService);
  
  selectedFile: File | null = null;
  isDragOver = false;
  isUploading = false;
  error = '';
  
  steps = [
    { number: 1, title: 'Upload', description: 'Envie seu livro em PDF, EPUB ou TXT' },
    { number: 2, title: 'Extração', description: 'O texto é extraído e dividido em capítulos' },
    { number: 3, title: 'Análise IA', description: 'GPT-4o analisa cada capítulo profundamente' },
    { number: 4, title: 'Download', description: 'Receba sua análise em Markdown ou PDF' }
  ];
  
  onDragOver(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }
  
  onDragLeave(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }
  
  onDrop(event: DragEvent) {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files && files.length > 0) {
      this.selectFile(files[0]);
    }
  }
  
  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      this.selectFile(input.files[0]);
    }
  }
  
  selectFile(file: File) {
    const validTypes = ['application/pdf', 'application/epub+zip', 'text/plain'];
    const validExtensions = ['.pdf', '.epub', '.txt'];
    
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!hasValidType && !hasValidExtension) {
      this.error = 'Formato não suportado. Use PDF, EPUB ou TXT.';
      return;
    }
    
    // 50MB limit
    if (file.size > 50 * 1024 * 1024) {
      this.error = 'Arquivo muito grande. Máximo 50MB.';
      return;
    }
    
    this.error = '';
    this.selectedFile = file;
  }
  
  clearFile(event: Event) {
    event.stopPropagation();
    this.selectedFile = null;
    this.error = '';
  }
  
  formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }
  
  uploadFile() {
    if (!this.selectedFile) return;
    
    this.isUploading = true;
    this.error = '';
    
    this.api.uploadBook(this.selectedFile).subscribe({
      next: (response) => {
        this.isUploading = false;
        this.router.navigate(['/status', response.job_id]);
      },
      error: (err) => {
        this.isUploading = false;
        this.error = err.error?.detail || 'Erro ao enviar arquivo. Tente novamente.';
      }
    });
  }
}

