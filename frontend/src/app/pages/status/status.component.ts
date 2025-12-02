import { Component, OnInit, OnDestroy, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { ApiService, JobStatus } from '../../services/api.service';

@Component({
  selector: 'app-status',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="container mx-auto px-6 py-12">
      <div class="max-w-3xl mx-auto">
        
        <!-- Back Button -->
        <a routerLink="/" class="inline-flex items-center gap-2 text-ink-400 hover:text-ink-200 mb-8 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          <span>Voltar</span>
        </a>
        
        <!-- Status Card -->
        <div class="card p-8 animate-fade-in">
          @if (loading) {
            <!-- Loading State -->
            <div class="flex flex-col items-center justify-center py-12">
              <div class="w-16 h-16 border-4 border-gold-500/20 border-t-gold-500 rounded-full animate-spin mb-6"></div>
              <p class="text-ink-400">Iniciando processamento...</p>
            </div>
          } @else if (error) {
            <!-- Error State -->
            <div class="text-center py-12">
              <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-wine-500/10 mb-6">
                <svg class="w-10 h-10 text-wine-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
                </svg>
              </div>
              <h2 class="text-2xl font-display font-bold text-ink-100 mb-4">Erro</h2>
              <p class="text-ink-400 mb-6">{{ error }}</p>
              <a routerLink="/" class="btn-primary">Tentar Novamente</a>
            </div>
          } @else if (status) {
            <!-- Status Content -->
            <div class="text-center mb-8">
              <!-- Status Icon -->
              <div class="inline-flex items-center justify-center w-24 h-24 rounded-2xl mb-6"
                   [class]="getStatusIconClass()">
                @switch (status.status) {
                  @case ('completed') {
                    <svg class="w-12 h-12 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  }
                  @case ('failed') {
                    <svg class="w-12 h-12 text-wine-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  }
                  @default {
                    <svg class="w-12 h-12 text-gold-500 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                            d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/>
                    </svg>
                  }
                }
              </div>
              
              <!-- Title -->
              <h1 class="text-3xl font-display font-bold text-ink-100 mb-2">
                {{ getStatusTitle() }}
              </h1>
              
              <!-- Metadata -->
              @if (status.metadata) {
                <p class="text-lg text-ink-400">
                  {{ status.metadata.title }}
                  @if (status.metadata.total_chapters > 0) {
                    <span class="text-ink-500"> · {{ status.metadata.total_chapters }} capítulos</span>
                  }
                </p>
              }
            </div>
            
            <!-- Progress Section -->
            @if (!isCompleted() && !isFailed()) {
              <div class="mb-8">
                <!-- Progress Bar -->
                <div class="progress-bar mb-3">
                  <div class="progress-bar-fill" [style.width.%]="status.progress"></div>
                </div>
                
                <!-- Progress Info -->
                <div class="flex justify-between text-sm">
                  <span class="text-ink-400">{{ status.current_step }}</span>
                  <span class="text-gold-400 font-medium">{{ status.progress | number:'1.0-0' }}%</span>
                </div>
              </div>
              
              <!-- Processing Steps -->
              <div class="grid grid-cols-5 gap-2 mb-8">
                @for (step of processingSteps; track step.key) {
                  <div class="text-center p-3 rounded-xl transition-all duration-300"
                       [class]="getStepClass(step.key)">
                    <div class="w-8 h-8 mx-auto mb-2 rounded-lg flex items-center justify-center"
                         [class]="getStepIconClass(step.key)">
                      @if (isStepComplete(step.key)) {
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                        </svg>
                      } @else if (isStepActive(step.key)) {
                        <div class="w-3 h-3 rounded-full bg-current animate-pulse"></div>
                      } @else {
                        <div class="w-2 h-2 rounded-full bg-current opacity-50"></div>
                      }
                    </div>
                    <span class="text-xs">{{ step.label }}</span>
                  </div>
                }
              </div>
            }
            
            <!-- Error Message -->
            @if (status.error_message) {
              <div class="p-4 rounded-xl bg-wine-500/10 border border-wine-500/30 mb-8">
                <p class="text-wine-400 text-center">{{ status.error_message }}</p>
              </div>
            }
            
            <!-- Download Section -->
            @if (isCompleted()) {
              <div class="border-t border-ink-700/30 pt-8">
                <h3 class="text-lg font-semibold text-ink-100 mb-6 text-center">
                  Download da Análise
                </h3>
                
                <div class="grid md:grid-cols-2 gap-4">
                  <!-- Markdown Download -->
                  @if (status.md_ready) {
                    <a [href]="api.getMarkdownDownloadUrl(jobId)" 
                       download
                       class="flex items-center gap-4 p-5 rounded-xl bg-ink-800/30 border border-ink-700/30 hover:border-gold-500/30 hover:bg-ink-800/50 transition-all group">
                      <div class="w-14 h-14 rounded-xl bg-ink-700/50 flex items-center justify-center group-hover:bg-gold-500/10 transition-colors">
                        <svg class="w-7 h-7 text-ink-300 group-hover:text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                        </svg>
                      </div>
                      <div class="flex-1">
                        <p class="font-semibold text-ink-100 group-hover:text-gold-300 transition-colors">Markdown</p>
                        <p class="text-sm text-ink-400">Análise completa em .md</p>
                      </div>
                      <svg class="w-5 h-5 text-ink-500 group-hover:text-gold-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                      </svg>
                    </a>
                  }
                  
                  <!-- PDF Download (se disponível) -->
                  @if (status.pdf_ready) {
                    <a [href]="api.getPdfDownloadUrl(jobId)" 
                       download
                       class="flex items-center gap-4 p-5 rounded-xl bg-ink-800/30 border border-ink-700/30 hover:border-wine-500/30 hover:bg-ink-800/50 transition-all group">
                      <div class="w-14 h-14 rounded-xl bg-ink-700/50 flex items-center justify-center group-hover:bg-wine-500/10 transition-colors">
                        <svg class="w-7 h-7 text-ink-300 group-hover:text-wine-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                                d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
                        </svg>
                      </div>
                      <div class="flex-1">
                        <p class="font-semibold text-ink-100 group-hover:text-wine-300 transition-colors">PDF</p>
                        <p class="text-sm text-ink-400">Análise formatada em .pdf</p>
                      </div>
                      <svg class="w-5 h-5 text-ink-500 group-hover:text-wine-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                      </svg>
                    </a>
                  }
                </div>
                
                <p class="text-xs text-ink-500 text-center mt-4">
                  ⚠️ Os arquivos serão excluídos automaticamente após o download
                </p>
                
                <!-- New Analysis -->
                <div class="mt-8 text-center">
                  <a routerLink="/" class="btn-secondary">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
                    </svg>
                    Nova Análise
                  </a>
                </div>
              </div>
            }
          }
        </div>
      </div>
    </div>
  `
})
export class StatusComponent implements OnInit, OnDestroy {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  api = inject(ApiService);
  
  jobId = '';
  status: JobStatus | null = null;
  loading = true;
  error = '';
  
  // Informações do upload passadas via navigation state
  private uploadInfo?: { fileUrl: string; filename: string; fileType: string };
  
  private processingSubscription?: Subscription;
  
  processingSteps = [
    { key: 'extracting', label: 'Extração' },
    { key: 'splitting', label: 'Capítulos' },
    { key: 'analyzing', label: 'Análise IA' },
    { key: 'generating', label: 'Geração' },
    { key: 'completed', label: 'Concluído' }
  ];
  
  ngOnInit() {
    this.jobId = this.route.snapshot.params['jobId'];
    
    if (!this.jobId) {
      this.router.navigate(['/']);
      return;
    }
    
    // Pega informações do upload do sessionStorage
    const storedData = sessionStorage.getItem(`job_${this.jobId}`);
    if (storedData) {
      try {
        this.uploadInfo = JSON.parse(storedData);
        console.log('Upload info from sessionStorage:', this.uploadInfo);
      } catch (e) {
        console.error('Error parsing stored upload info:', e);
      }
    }
    
    // Inicia o processamento automaticamente
    this.startProcessing();
  }
  
  ngOnDestroy() {
    this.processingSubscription?.unsubscribe();
    this.api.cancelProcessing();
  }
  
  private startProcessing() {
    this.loading = false;
    
    // Inicia com status pendente
    this.status = {
      job_id: this.jobId,
      status: 'pending',
      progress: 0,
      current_step: 'Iniciando processamento...',
      output_ready: false
    };
    
    // Processa o livro (orquestra todas as etapas)
    // Passa as informações do upload se disponíveis
    this.processingSubscription = this.api.processBook(
      this.jobId,
      (status) => {
        // Callback de progresso
        this.status = status;
      },
      this.uploadInfo
    ).subscribe({
      next: (finalStatus) => {
        this.status = finalStatus;
      },
      error: (err) => {
        this.error = err.message || 'Erro no processamento';
        if (this.status) {
          this.status.status = 'failed';
          this.status.error_message = this.error;
        }
      }
    });
  }
  
  isCompleted(): boolean {
    return this.status?.status === 'completed' && this.status?.output_ready === true;
  }
  
  isFailed(): boolean {
    return this.status?.status === 'failed';
  }
  
  getStatusTitle(): string {
    switch (this.status?.status) {
      case 'completed': return 'Análise Concluída!';
      case 'failed': return 'Erro no Processamento';
      case 'extracting': return 'Extraindo Texto...';
      case 'splitting': return 'Dividindo em Capítulos...';
      case 'analyzing': return 'Analisando com IA...';
      case 'generating': return 'Gerando Documentos...';
      default: return 'Processando...';
    }
  }
  
  getStatusIconClass(): string {
    switch (this.status?.status) {
      case 'completed': return 'bg-emerald-500/10';
      case 'failed': return 'bg-wine-500/10';
      default: return 'bg-gold-500/10';
    }
  }
  
  private getStepOrder(key: string): number {
    const order: Record<string, number> = {
      'pending': 0,
      'extracting': 1,
      'splitting': 2,
      'analyzing': 3,
      'generating': 4,
      'completed': 5,
      'failed': -1
    };
    return order[key] ?? 0;
  }
  
  isStepComplete(stepKey: string): boolean {
    if (!this.status) return false;
    return this.getStepOrder(this.status.status) > this.getStepOrder(stepKey);
  }
  
  isStepActive(stepKey: string): boolean {
    return this.status?.status === stepKey;
  }
  
  getStepClass(stepKey: string): string {
    if (this.isStepComplete(stepKey)) {
      return 'bg-emerald-500/10 text-emerald-400';
    }
    if (this.isStepActive(stepKey)) {
      return 'bg-gold-500/10 text-gold-400';
    }
    return 'bg-ink-800/30 text-ink-500';
  }
  
  getStepIconClass(stepKey: string): string {
    if (this.isStepComplete(stepKey)) {
      return 'bg-emerald-500/20 text-emerald-400';
    }
    if (this.isStepActive(stepKey)) {
      return 'bg-gold-500/20 text-gold-400';
    }
    return 'bg-ink-700/50 text-ink-500';
  }
}
