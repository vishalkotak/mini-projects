#[derive(Debug)]
struct Deck {
    cards: Vec<String>,
}

impl Deck {
    fn new() -> Self {
        let suites = ["Hearts", "Spades"];
        let values = ["Ace", "Two", "Three"];

        let mut cards: Vec<String> = Vec::new();


        for suit in suites {
            for value in values {
                let card = format!("{} of {}", value, suit);
                cards.push(card);
            }
        }

        let deck: Deck = Deck { cards: cards };
        return deck;
    }
}

fn main() {

    let deck: Deck = Deck::new();

    println!("Heres your deck: {:#?}", deck);
}
