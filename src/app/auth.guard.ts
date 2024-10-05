// import { CanActivateFn } from '@angular/router';

// export const authGuard: CanActivateFn = (
//   route, state
  
//   ) => {
//   console.log('Le guard a bien été appelé!');
//   return true;
// };

import { Injectable } from '@angular/core';
import { CanActivate, Router, } from '@angular/router';
import { AuthService } from './auth.service';


@Injectable({
  providedIn:'root'
})

export class AuthGuard implements CanActivate {
  constructor(
    private authService:AuthService,
    private router : Router
  ){}
  canActivate() :boolean{
   if (this.authService.isLoggedIn) {
    return true ;
   }
   this.router.navigate(['/login'])
    return false ;
  }
}



