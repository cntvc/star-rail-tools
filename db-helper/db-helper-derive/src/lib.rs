use proc_macro::TokenStream;
use quote::quote;
use syn::{Data, DeriveInput, Error, Fields, Result, parse_macro_input, spanned::Spanned};

#[proc_macro_derive(FromRow)]
pub fn derive_from_row(input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as DeriveInput);

    let struct_name = &input.ident;
    let generics = &input.generics;

    let fields = match get_named_fields(&input.data) {
        Ok(fields) => fields,
        Err(e) => return e.to_compile_error().into(),
    };

    let field_assignments = fields.iter().map(|field| {
        let field_name = field.ident.as_ref().unwrap();
        let field_name_str = field_name.to_string();

        quote! {
            #field_name: row.get(#field_name_str)?
        }
    });

    let (impl_generics, ty_generics, where_clause) = generics.split_for_impl();

    let expanded = quote! {
        impl #impl_generics db_helper::FromRow for #struct_name #ty_generics #where_clause {
            fn from_row(row: &rusqlite::Row) -> rusqlite::Result<Self> {
                Ok(Self {
                    #(#field_assignments),*
                })
            }
        }
    };

    TokenStream::from(expanded)
}

fn get_named_fields(
    data: &Data,
) -> Result<&syn::punctuated::Punctuated<syn::Field, syn::Token![,]>> {
    match data {
        Data::Struct(s) => match &s.fields {
            Fields::Named(named_fields) => Ok(&named_fields.named),
            _ => Err(Error::new(
                s.fields.span(),
                "FromRow macro only supports structs with named fields",
            )),
        },
        Data::Enum(e) => Err(Error::new(
            e.enum_token.span(),
            "FromRow macro only supports structs with named fields",
        )),
        Data::Union(u) => Err(Error::new(
            u.union_token.span(),
            "FromRow macro only supports structs with named fields",
        )),
    }
}
