import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [RouterLink],
  template: `
    <header class="relative z-20 py-6">
      <div class="container mx-auto px-6">
        <nav class="flex items-center justify-between">
          <!-- Logo -->
          <a routerLink="/" class="flex items-center gap-3 group">
            <div class="relative">
              <!-- Book Icon -->
              <svg class="w-10 h-10 text-gold-500 group-hover:text-gold-400 transition-colors duration-300" 
                   viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" 
                      stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <!-- Glow effect -->
              <div class="absolute inset-0 blur-xl bg-gold-500/30 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
            </div>
            <div>
              <span class="text-2xl font-display font-bold text-gradient">BooksMD</span>
              <span class="block text-xs text-ink-400 -mt-1">Análise Inteligente</span>
            </div>
          </a>
          
          <!-- Actions -->
          <div class="flex items-center gap-4">
            <a href="https://github.com" target="_blank" 
               class="p-2 rounded-lg text-ink-400 hover:text-ink-200 hover:bg-ink-800/50 transition-all duration-300">
              <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fill-rule="evenodd" clip-rule="evenodd" 
                      d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
              </svg>
            </a>
          </div>
        </nav>
      </div>
    </header>
  `
})
export class HeaderComponent {}

