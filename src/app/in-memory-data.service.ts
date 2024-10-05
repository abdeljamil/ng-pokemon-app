import { Injectable } from '@angular/core';
import { POKEMONS } from './pokemon/mock-pokemon-list';

@Injectable({
  providedIn: 'root'
})
export class InMemoryDataService implements InMemoryDataService {

  createDb() {
    const pokemons = POKEMONS;
    return {pokemons};
  }
}
