import { Component, OnInit, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { FormsModule } from '@angular/forms';

export interface LineupStat {
  lineup: string;
  possessions: number;
  offensive_rating: number;
  defensive_rating: number;
  net_rating: number;
}

@Component({
  selector: 'app-lineups-summary',
  standalone: true,
  imports: [
    CommonModule, 
    MatTableModule, 
    MatSortModule, 
    MatFormFieldModule, 
    MatSelectModule, 
    FormsModule
  ],
  templateUrl: './lineups-summary.component.html',
  styleUrls: ['./lineups-summary.component.scss']
})
export class LineupsSummaryComponent implements OnInit {
  isLoading = true;
  leagueLineupSize = 5;
  
  // Dropdown options for different n-man lineups
  lineupSizes = [
    { value: 1, label: '1-man' },
    { value: 2, label: '2-man' },
    { value: 3, label: '3-man' },
    { value: 4, label: '4-man' },
    { value: 5, label: '5-man' }
  ];

  displayedColumns: string[] = ['lineup', 'possessions', 'offensive_rating', 'defensive_rating', 'net_rating'];
  dataSource = new MatTableDataSource<LineupStat>([]);

  @ViewChild(MatSort) set matSort(sort: MatSort) {
    this.dataSource.sort = sort;
  }

  private http = inject(HttpClient);

  ngOnInit(): void {
    this.fetchLineups();
  }

fetchLineups(): void {
    this.isLoading = true;
    const apiUrl = `http://127.0.0.1:8000/api/v1/lineups?lineup_size=${this.leagueLineupSize}`;

    // Notice we changed this to <any[]> since the raw data shape doesn't perfectly match yet
    this.http.get<any[]>(apiUrl).subscribe({
      next: (data) => {
        
        // Map the backend's naming to match our frontend's expected LineupStat interface
        const formattedData: LineupStat[] = data.map(item => ({
          // Loop through the 5 players and combine their names into a single string
          lineup: item.players.map((p: any) => p.name).join(', '), 
          possessions: item.total_possessions,
          offensive_rating: item.offensive_rating,
          defensive_rating: item.defensive_rating,
          net_rating: item.net_rating
        }));

        this.dataSource.data = formattedData;
        this.isLoading = false;
      },
      error: (err) => {
        console.error('Failed to fetch from Django:', err);
        this.isLoading = false;
      }
    });
  }

  onSizeChange(): void {
    this.fetchLineups(); // Re-fetch data when dropdown changes
  }
  
  
  }

