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
  selector: 'app-login',
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
    <div class="login-container">
      <p-card header="UzGidroChat" subheader="Вход в систему" class="login-card">
        <div class="form-group">
          <label for="username">Логин</label>
          <input type="text" pInputText id="username" [(ngModel)]="username" placeholder="Введите логин" class="w-full" />
        </div>
        
        <div class="form-group">
          <label for="password">Пароль</label>
          <p-password id="password" [(ngModel)]="password" placeholder="Введите пароль" [feedback]="false" [toggleMask]="true" styleClass="w-full" />
        </div>

        @if (error) {
          <p-message severity="error" [text]="error" class="w-full mb-3" />
        }

        <div class="buttons">
          <p-button label="Войти" (click)="login()" [loading]="loading" class="w-full" />
        </div>

        <div class="register-link">
          <span>Нет аккаунта? </span>
          <a routerLink="/register">Зарегистрироваться</a>
        </div>
      </p-card>
    </div>
  `,
  styles: [`
    .login-container {
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 100vh;
      background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
    }
    .login-card {
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
    .register-link {
      text-align: center;
      margin-top: 1rem;
    }
    .register-link a {
      color: #2196F3;
      text-decoration: none;
    }
    .mb-3 {
      margin-bottom: 1rem;
    }
  `]
})
export class LoginComponent {
  username = '';
  password = '';
  loading = false;
  error = '';

  constructor(private authService: AuthService, private router: Router) {}

  login(): void {
    if (!this.username || !this.password) {
      this.error = 'Заполните все поля';
      return;
    }

    this.loading = true;
    this.error = '';

    this.authService.login(this.username, this.password).subscribe({
      next: () => {
        this.router.navigate(['/chat']);
      },
      error: (err) => {
        this.error = err.error?.detail || 'Ошибка входа';
        this.loading = false;
      }
    });
  }
}