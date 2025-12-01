import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-particles',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="floating-particles">
      @for (particle of particles; track particle.id) {
        <div 
          class="particle"
          [style.left.%]="particle.x"
          [style.animationDelay.s]="particle.delay"
          [style.animationDuration.s]="particle.duration"
          [style.width.px]="particle.size"
          [style.height.px]="particle.size"
          [style.opacity]="particle.opacity">
        </div>
      }
    </div>
  `
})
export class ParticlesComponent implements OnInit {
  particles: Array<{
    id: number;
    x: number;
    delay: number;
    duration: number;
    size: number;
    opacity: number;
  }> = [];

  ngOnInit() {
    // Generate random particles
    for (let i = 0; i < 20; i++) {
      this.particles.push({
        id: i,
        x: Math.random() * 100,
        delay: Math.random() * 15,
        duration: 15 + Math.random() * 10,
        size: 2 + Math.random() * 4,
        opacity: 0.1 + Math.random() * 0.3
      });
    }
  }
}

