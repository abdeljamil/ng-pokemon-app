import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, Subject, debounceTime, distinctUntilChanged, switchMap } from 'rxjs';
import { Pokemon } from '../pokemon';
import { PokemonService } from '../pokemon.service';

@Component({
  selector: 'app-search-pokemon',
  templateUrl: './search-pokemon.component.html',
  styles: [
  ]
})
export class SearchPokemonComponent implements OnInit {

  searchTerms = new Subject<string>();
  pokemon$:Observable<Pokemon[]>;

  constructor(
    private router :Router,
    private pokemonService:PokemonService
    ){}


  ngOnInit(): void {

    this.pokemon$ = this.searchTerms.pipe(
      debounceTime(300),

      distinctUntilChanged(),

      switchMap((term) => this.pokemonService.searchPokemonList(term))
    );
  }



  search(term:string){
    this.searchTerms.next(term);
  }

  goToDetail(pokemon:Pokemon){
    const link = ['/pokemon',pokemon.id];
    this.router.navigate(link)
  }

}
 