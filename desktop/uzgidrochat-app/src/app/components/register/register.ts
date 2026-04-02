import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { CardModule } from 'primeng/card';
import { MessageModule } from 'primeng/message';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    ButtonModule,
    InputTextModule,
    PasswordModule,
    CardModule,
    MessageModule
  ],
  template: `
    <div class="register-container">
      <p-card header="UzGidroChat" subheader="Регистрация" class="register-card">
        <div class="form-group">
          <label for="fullName">Полное имя</label>
          <input type="text" pInputText id="fullName" [(ngModel)]="fullName" placeholder="Введите имя" class="w-full" />
        </div>

        <div class="form-group">
          <label for="username">Логин</label>
          <input type="text" pInputText id="username" [(ngModel)]="username" placeholder="Введите логин" class="w-full" />
        </div>

        <div class="form-group">
          <label for="email">Email</label>
          <input type="email" pInputText id="email" [(ngModel)]="email" placeholder="Введите email" class="w-full" />
        </div>
        
        <div class="form-group">
          <label for="password">Пароль</label>
          <p-password id="password" [(ngModel)]="password" placeholder="Введите пароль" [toggleMask]="true" styleClass="w-full" />
        </div>

        @if (error) {
          <p-message severity="error" [text]="error" class="w-full mb-3" />
        }

        @if (success) {
          <p-message severity="success" text="Регистрация успешна! Перенаправление..." class="w-full mb-3" />
        }

        <div class="buttons">
          <p-button label="Зарегистрироваться" (click)="register()" [loading]="loading" class="w-full" />
        </div>

        <div class="login-link">
          <span>Уже есть аккаунт? </span>
          <a routerLink="/login">Войти</a>
        </div>
      </p-card>
    </div>
  `,
  styles: [`
    .register-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    }
    .register-card {
      width: 400px;
    }
    .form-group {
      margin-bottom: 1.5rem;
    }
    .form-group label {
      display: block;
      margin-bottom: 0.5rem;
      font-weight: 500;
    }
    .w-full {
      width: 100%;
    }
    .buttons {
      margin-top: 1.5rem;
    }
    .login-link {
      text-align: center;
      margin-top: 1rem;
    }
    .login-link a {
      color: #2196F3;
      text-decoration: none;
    }
    .mb-3 {
      margin-bottom: 1rem;
    }
  `]
})
export class RegisterComponent {
  fullName = '';
  username = '';
  email = '';
  password = '';
  loading = false;
  error = '';
  success = false;

  constructor(private authService: AuthService, private router: Router) {}

  register(): void {
    if (!this.fullName || !this.username || !this.email || !this.password) {
      this.error = 'Заполните все поля';
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.register(this.username, this.email, this.password, this.fullName).subscribe({
      next: () => {
        this.success = true;
        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 1500);
      },
      error: (err) => {
        this.error = err.error?.detail || 'Ошибка регистрации';
        this.loading = false;
      }
    });
  }
}