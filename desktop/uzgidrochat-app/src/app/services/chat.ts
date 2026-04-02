import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';


// В Electron используем прямой адрес сервера, в браузере — относительный URL (nginx проксирует)
const isElectron = navigator.userAgent.includes('Electron');
const API_URL = isElectron ? 'http://10.0.90.92:8000' : '';
const WS_URL = isElectron ? 'ws://10.0.90.92:8000' : `ws://${window.location.host}`;

export interface Message {
  id: number;
  content: string | null;
  sender_id: number;
  receiver_id: number | null;
  group_id: number | null;
  is_read: boolean;
  is_edited: boolean;
  is_deleted: boolean;
  created_at: string;
  edited_at: string | null;
  file_name: string | null;
  file_path: string | null;
  file_type: string | null;
  reply_to_id: number | null;
  reply_to?: Message | null;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  is_online: boolean;
  last_seen: string | null;
  avatar_path: string | null;
  created_at: string;
}

export interface Group {
  id: number;
  name: string;
  description: string | null;
  creator_id: number;
  created_at: string;
  members: User[];
}

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private socket: WebSocket | null = null;
  private messagesSubject = new Subject<any>();
  public messages$ = this.messagesSubject.asObservable();
  public apiUrl = API_URL;

  constructor(private http: HttpClient) {}

  connectWebSocket(userId: number): void {
  this.socket = new WebSocket(`${WS_URL}/ws/${userId}`);
  
  this.socket.onopen = () => {
    console.log('WebSocket подключён');
  };
  
  this.socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    this.messagesSubject.next(data);
  };
  
  this.socket.onclose = () => {
    console.log('WebSocket отключён');
  };
}

sendTypingStatus(receiverId: number, isTyping: boolean): void {
  if (this.socket && this.socket.readyState === WebSocket.OPEN) {
    this.socket.send(JSON.stringify({
      type: 'typing',
      receiver_id: receiverId,
      is_typing: isTyping
    }));
  }
}

  disconnectWebSocket(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  // Users
  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(`${API_URL}/users`);
  }

  // Personal messages
  getMessages(userId: number, otherUserId: number): Observable<Message[]> {
    return this.http.get<Message[]>(`${API_URL}/messages/${userId}/${otherUserId}`);
  }

  sendMessage(senderId: number, receiverId: number | null, content: string, groupId: number | null, replyToId: number | null = null): Observable<Message> {
  return this.http.post<Message>(`${API_URL}/messages`, {
    sender_id: senderId,
    receiver_id: receiverId,
    content: content,
    group_id: groupId,
    reply_to_id: replyToId
  });
}

  // Upload file
  uploadFile(file: File, userId: number, receiverId: number | null, groupId: number | null): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    
    let url = `${API_URL}/messages/upload?user_id=${userId}`;
    if (receiverId) {
      url += `&receiver_id=${receiverId}`;
    }
    if (groupId) {
      url += `&group_id=${groupId}`;
    }
    
    return this.http.post(url, formData);
  }

  // Groups
  getGroups(userId: number): Observable<Group[]> {
    return this.http.get<Group[]>(`${API_URL}/groups?user_id=${userId}`);
  }

  createGroup(creatorId: number, name: string, description: string, memberIds: number[]): Observable<Group> {
    return this.http.post<Group>(`${API_URL}/groups?creator_id=${creatorId}`, {
      name,
      description,
      member_ids: memberIds
    });
  }

  getGroupMessages(groupId: number): Observable<Message[]> {
    return this.http.get<Message[]>(`${API_URL}/messages/group/${groupId}`);
  }
  // Edit message
editMessage(messageId: number, userId: number, content: string): Observable<Message> {
  return this.http.put<Message>(`${API_URL}/messages/${messageId}?user_id=${userId}`, {
    content
  });
}

// Delete message
deleteMessage(messageId: number, userId: number): Observable<any> {
  return this.http.delete(`${API_URL}/messages/${messageId}?user_id=${userId}`);
}
// Avatar
uploadAvatar(userId: number, file: File): Observable<any> {
  const formData = new FormData();
  formData.append('file', file);
  return this.http.post(`${API_URL}/users/${userId}/avatar`, formData);
}

deleteAvatar(userId: number): Observable<any> {
  return this.http.delete(`${API_URL}/users/${userId}/avatar`);
}

  addGroupMembers(groupId: number, userIds: number[]): Observable<any> {
    return this.http.post(`${API_URL}/groups/${groupId}/members`, {
      user_ids: userIds
    });
  }

  removeGroupMember(groupId: number, userId: number): Observable<any> {
    return this.http.delete(`${API_URL}/groups/${groupId}/members/${userId}`);
  }
}