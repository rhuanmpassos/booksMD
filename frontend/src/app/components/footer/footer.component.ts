import { Component } from '@angular/core';

@Component({
  selector: 'app-footer',
  standalone: true,
  template: `
    <footer class="relative z-10 py-8 border-t border-ink-800/50">
      <div class="container mx-auto px-6">
        <div class="flex flex-col md:flex-row items-center justify-between gap-4">
          <!-- Copyright -->
          <p class="text-ink-500 text-sm">
            © 2024 BooksMD. Transformando livros em conhecimento.
          </p>
          
          <!-- Tech Stack -->
          <div class="flex items-center gap-6 text-ink-500 text-sm">
            <span class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-emerald-500"></span>
              Powered by GPT-4o
            </span>
            <span>Angular + Tailwind</span>
            <span>FastAPI</span>
          </div>
        </div>
      </div>
    </footer>
  `
})
export class FooterComponent {}

