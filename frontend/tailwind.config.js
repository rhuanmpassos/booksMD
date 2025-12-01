/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        // Paleta principal - Tons de tinta e papel
        ink: {
          50: '#f7f6f4',
          100: '#eeedea',
          200: '#dddbd6',
          300: '#c4c1b9',
          400: '#a8a49a',
          500: '#918c81',
          600: '#7a756c',
          700: '#65615a',
          800: '#55524c',
          900: '#494642',
          950: '#272523',
        },
        // Accent - Dourado literário
        gold: {
          50: '#fdfaeb',
          100: '#faf2c7',
          200: '#f5e38b',
          300: '#f0cf4f',
          400: '#ebba24',
          500: '#dba014',
          600: '#be7a0e',
          700: '#97570f',
          800: '#7c4414',
          900: '#693917',
          950: '#3d1d08',
        },
        // Accent secundário - Vermelho vinho
        wine: {
          50: '#fdf3f3',
          100: '#fce4e4',
          200: '#fbcdcd',
          300: '#f6abab',
          400: '#ee7a7a',
          500: '#e24f4f',
          600: '#ce3232',
          700: '#ad2626',
          800: '#8f2323',
          900: '#772323',
          950: '#400e0e',
        },
      },
      fontFamily: {
        'display': ['Playfair Display', 'Georgia', 'serif'],
        'body': ['Source Serif 4', 'Georgia', 'serif'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-up': 'slideUp 0.5s ease-out',
        'fade-in': 'fadeIn 0.6s ease-out',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(219, 160, 20, 0.3)' },
          '100%': { boxShadow: '0 0 25px rgba(219, 160, 20, 0.6)' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
      backgroundImage: {
        'paper-texture': "url('/assets/paper-texture.png')",
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}

