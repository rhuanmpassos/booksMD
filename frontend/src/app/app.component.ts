import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HeaderComponent } from './components/header/header.component';
import { FooterComponent } from './components/footer/footer.component';
import { ParticlesComponent } from './components/particles/particles.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HeaderComponent, FooterComponent, ParticlesComponent],
  template: `
    <div class="relative min-h-screen flex flex-col">
      <!-- Background Particles -->
      <app-particles />
      
      <!-- Header -->
      <app-header />
      
      <!-- Main Content -->
      <main class="flex-1 relative z-10">
        <router-outlet />
      </main>
      
      <!-- Footer -->
      <app-footer />
    </div>
  `
})
export class AppComponent {}

